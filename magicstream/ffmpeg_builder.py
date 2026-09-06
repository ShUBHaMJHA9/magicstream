"""
FFmpeg Command Builder & Filtergraph Generator for MagicStream
Author: Shubham Kumar Jha
License: MIT

Constructs optimized FFmpeg commands for all streaming modes,
supports real-time SVG/PNG watermark overlays, hardware acceleration,
adaptive quality profiles, and proper FLV/RTMP stream packetization.
"""

import os
import shutil
from typing import Dict, Any, List, Optional
from magicstream.hardware import HardwareDetector, QUALITY_PROFILES


class FFmpegBuilder:
    """Builds robust FFmpeg command strings and arguments with adaptive quality."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"

    _cached_encoder: Optional[str] = None

    def detect_encoder(self, hw_accel: str = "auto") -> str:
        """Determines the best available video encoder on the current OS."""
        hw_accel = hw_accel.lower()
        if hw_accel in ("nvenc", "h264_nvenc"):
            return "h264_nvenc"
        elif hw_accel in ("vaapi", "h264_vaapi"):
            return "h264_vaapi"
        elif hw_accel in ("libx264", "x264"):
            return "libx264"
        elif hw_accel in ("libopenh264", "openh264"):
            return "libopenh264"

        if FFmpegBuilder._cached_encoder:
            return FFmpegBuilder._cached_encoder

        try:
            import subprocess
            res = subprocess.run(
                [self.ffmpeg_path, "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3,
            )
            output = res.stdout or ""
            # Priority: libx264 -> libopenh264 -> h264_nvenc -> h264_vaapi
            for candidate in ["libx264", "libopenh264", "h264_nvenc", "h264_vaapi"]:
                if candidate in output:
                    FFmpegBuilder._cached_encoder = candidate
                    return candidate
        except Exception:
            pass

        FFmpegBuilder._cached_encoder = "libx264"
        return "libx264"


    def resolve_quality_params(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Resolves active encoding parameters based on user config or adaptive auto-detection."""
        enc_cfg = self.config.get("encoding", {})
        configured_profile = profile_name or enc_cfg.get("quality_profile", "auto")

        base_profile = HardwareDetector.get_profile(configured_profile)
        result = dict(base_profile)

        if "resolution" in enc_cfg and configured_profile not in QUALITY_PROFILES:
            result["resolution"] = enc_cfg["resolution"]
        if "fps" in enc_cfg and configured_profile not in QUALITY_PROFILES:
            result["fps"] = enc_cfg["fps"]
        if "video_bitrate" in enc_cfg and configured_profile not in QUALITY_PROFILES:
            result["video_bitrate"] = enc_cfg["video_bitrate"]

        return result

    def build_overlay_filter(
        self,
        logo_input_index: Optional[int] = None,
        banner_input_index: Optional[int] = None,
        resolution: str = "1920x1080",
        scale_width: int = 200,
        position: str = "top-right",
        margin_x: int = 24,
        margin_y: int = 24,
        opacity: float = 0.92,
        max_allowed_logo_width: int = 200,
        banner_scale_width: Optional[int] = None,
        banner_position: str = "bottom-left",
    ) -> str:
        """Builds a complex filter string for scaling, opacity, and positioning of logo and/or lower-third banners."""
        res_colon = resolution.replace("x", ":")
        res_w = int(resolution.split("x")[0]) if "x" in resolution else 1920

        def calc_coords(pos: str, mx: int, my: int) -> str:
            p = pos.lower().strip()
            if p == "top-left":
                return f"x={mx}:y={my}"
            elif p == "bottom-right":
                return f"x=W-w-{mx}:y=H-h-{my}"
            elif p == "bottom-left":
                return f"x={mx}:y=H-h-{my}"
            elif p == "bottom-center":
                return f"x=(W-w)/2:y=H-h-{my}"
            elif p == "center":
                return "x=(W-w)/2:y=(H-h)/2"
            else:
                return f"x=W-w-{mx}:y={my}"

        filters = [f"[0:v]scale={res_colon},format=yuv420p[base]"]
        current_base = "[base]"

        # 1. Logo Watermark Layer
        if logo_input_index is not None:
            eff_w = min(scale_width, max_allowed_logo_width) if scale_width > 0 else max_allowed_logo_width
            scale_str = f"scale={eff_w}:-1" if eff_w > 0 else "null"
            alpha_str = f"colorchannelmixer=aa={opacity:.2f}"
            logo_coords = calc_coords(position, margin_x, margin_y)
            filters.append(f"[{logo_input_index}:v]format=rgba,{scale_str},{alpha_str}[watermark]")
            if banner_input_index is not None:
                filters.append(f"{current_base}[watermark]overlay={logo_coords}[tmp_base]")
                current_base = "[tmp_base]"
            else:
                filters.append(f"{current_base}[watermark]overlay={logo_coords}[outv]")
                return ";".join(filters)

        # 2. Lower-Third Banner Layer (Music Now Playing or News Ticker)
        if banner_input_index is not None:
            if banner_position == "fullscreen":
                filters.append(f"[{banner_input_index}:v]format=rgba,scale={res_w}:{res_h}[banner]")
                filters.append(f"{current_base}[banner]overlay=0:0[outv]")
                return ";".join(filters)

            if banner_scale_width is None:
                if res_w >= 1920:
                    b_w = 820
                elif res_w >= 1280:
                    b_w = 620
                elif res_w >= 854:
                    b_w = 440
                else:
                    b_w = 280
            else:
                b_w = min(banner_scale_width, res_w - 20)

            scaled_mx = max(8, int(margin_x * (res_w / 1920)))
            scaled_my = max(8, int(margin_y * (res_w / 1920)))
            banner_coords = calc_coords(banner_position, scaled_mx, scaled_my)
            filters.append(f"[{banner_input_index}:v]format=rgba,scale={b_w}:-1,colorchannelmixer=aa=0.96[banner]")
            filters.append(f"{current_base}[banner]overlay={banner_coords}[outv]")
            return ";".join(filters)

        return f"[0:v]scale={res_colon},format=yuv420p[outv]"

    def build_radio_command(
        self,
        video_path: str,
        audio_url: str,
        destination_url: str,
        loop_video: bool = True,
        profile_override: Optional[str] = None,
        banner_path: Optional[str] = None,
    ) -> List[str]:
        """Mode 1 & Mode 3: Radio Looper / Custom Combiner with adaptive quality and on-screen cards."""
        enc_params = self.resolve_quality_params(profile_override)
        overlay_cfg = self.config.get("overlay", {})

        resolution = enc_params["resolution"]
        fps = str(enc_params["fps"])
        preset = enc_params["preset"]
        video_bitrate = enc_params["video_bitrate"]
        max_rate = enc_params["max_rate"]
        buf_size = enc_params["buf_size"]
        gop_size = str(enc_params["gop_size"])
        threads = enc_params.get("threads", 0)

        audio_codec = enc_params.get("audio_codec", "aac")
        audio_bitrate = enc_params.get("audio_bitrate", "128k")
        audio_sample_rate = str(enc_params.get("audio_sample_rate", 44100))

        encoder = self.detect_encoder(self.config.get("encoding", {}).get("hw_accel", "auto"))

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "info",
            "-re",
        ]

        if threads > 0:
            cmd.extend(["-threads", str(threads)])

        if loop_video:
            cmd.extend(["-stream_loop", "-1"])
        cmd.extend(["-i", video_path])

        if audio_url.startswith(("http://", "https://")):
            cmd.extend([
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
            ])
        cmd.extend(["-i", audio_url])

        enable_overlay = overlay_cfg.get("enable", True)
        logo_path = overlay_cfg.get("logo_path", "logo/logo.svg")
        has_logo = enable_overlay and os.path.exists(logo_path)
        has_banner = banner_path and os.path.exists(banner_path)

        next_input_idx = 2
        logo_idx = None
        banner_idx = None

        if has_logo:
            cmd.extend(["-stream_loop", "-1", "-i", logo_path])
            logo_idx = next_input_idx
            next_input_idx += 1

        if has_banner:
            cmd.extend(["-stream_loop", "-1", "-i", banner_path])
            banner_idx = next_input_idx
            next_input_idx += 1

        if logo_idx is not None or banner_idx is not None:
            now_playing_pos = overlay_cfg.get("now_playing", {}).get("position", "bottom-left")
            filter_str = self.build_overlay_filter(
                logo_input_index=logo_idx,
                banner_input_index=banner_idx,
                resolution=resolution,
                scale_width=overlay_cfg.get("scale_width", 200),
                position=overlay_cfg.get("position", "top-right"),
                margin_x=overlay_cfg.get("margin_x", 24),
                margin_y=overlay_cfg.get("margin_y", 24),
                opacity=overlay_cfg.get("opacity", 0.92),
                max_allowed_logo_width=enc_params.get("max_logo_width", 200),
                banner_position=now_playing_pos,
            )
            cmd.extend(["-filter_complex", filter_str, "-map", "[outv]", "-map", "1:a"])
        else:
            res_colon = resolution.replace("x", ":")
            cmd.extend([
                "-vf", f"scale={res_colon},format=yuv420p",
                "-map", "0:v",
                "-map", "1:a",
            ])

        cmd.extend(["-c:v", encoder])
        if encoder == "libx264":
            cmd.extend(["-preset", preset, "-tune", "zerolatency"])
        elif encoder == "h264_nvenc":
            cmd.extend(["-preset", "p4", "-tune", "ll"])

        cmd.extend([
            "-b:v", video_bitrate,
            "-maxrate", max_rate,
            "-bufsize", buf_size,
            "-r", fps,
            "-g", gop_size,
            "-keyint_min", gop_size,
            "-sc_threshold", "0",
            "-pix_fmt", "yuv420p",
            "-c:a", audio_codec,
            "-b:a", audio_bitrate,
            "-ar", audio_sample_rate,
            "-ac", "2",
            "-af", "aresample=async=1",
            "-shortest",
            "-flvflags", "no_duration_filesize",
            "-f", "flv",
            destination_url,
        ])

        return cmd

    def build_relay_command(
        self,
        video_source_url: str,
        audio_source_url: Optional[str],
        destination_url: str,
        is_live: bool = True,
        profile_override: Optional[str] = None,
    ) -> List[str]:
        """Mode 2 & Mode 5: Restream / Relay an existing live stream with adaptive quality."""
        enc_params = self.resolve_quality_params(profile_override)
        overlay_cfg = self.config.get("overlay", {})

        resolution = enc_params["resolution"]
        fps = str(enc_params["fps"])
        preset = enc_params["preset"]
        video_bitrate = enc_params["video_bitrate"]
        max_rate = enc_params["max_rate"]
        buf_size = enc_params["buf_size"]
        gop_size = str(enc_params["gop_size"])
        threads = enc_params.get("threads", 0)

        audio_codec = enc_params.get("audio_codec", "aac")
        audio_bitrate = enc_params.get("audio_bitrate", "128k")
        audio_sample_rate = str(enc_params.get("audio_sample_rate", 44100))

        encoder = self.detect_encoder(self.config.get("encoding", {}).get("hw_accel", "auto"))

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "info",
        ]

        if threads > 0:
            cmd.extend(["-threads", str(threads)])

        if not is_live:
            cmd.append("-re")

        if video_source_url.startswith(("http://", "https://")):
            cmd.extend([
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5",
            ])
        cmd.extend(["-i", video_source_url])

        separate_audio = audio_source_url and audio_source_url != video_source_url
        if separate_audio:
            if audio_source_url.startswith(("http://", "https://")):
                cmd.extend([
                    "-reconnect", "1",
                    "-reconnect_at_eof", "1",
                    "-reconnect_streamed", "1",
                    "-reconnect_delay_max", "5",
                ])
            cmd.extend(["-i", audio_source_url])

        enable_overlay = overlay_cfg.get("enable", True)
        logo_path = overlay_cfg.get("logo_path", "logo/logo.svg")
        has_logo = enable_overlay and os.path.exists(logo_path)

        logo_input_index = 2 if separate_audio else 1
        audio_map_index = "1:a" if separate_audio else "0:a"

        if has_logo:
            cmd.extend(["-stream_loop", "-1", "-i", logo_path])
            filter_str = self.build_overlay_filter(
                logo_input_index=logo_input_index,
                resolution=resolution,
                scale_width=overlay_cfg.get("scale_width", 200),
                position=overlay_cfg.get("position", "top-right"),
                margin_x=overlay_cfg.get("margin_x", 24),
                margin_y=overlay_cfg.get("margin_y", 24),
                opacity=overlay_cfg.get("opacity", 0.92),
                max_allowed_logo_width=enc_params.get("max_logo_width", 200),
            )
            cmd.extend(["-filter_complex", filter_str, "-map", "[outv]", "-map", audio_map_index])
        else:
            res_colon = resolution.replace("x", ":")
            cmd.extend([
                "-vf", f"scale={res_colon},format=yuv420p",
                "-map", "0:v",
                "-map", audio_map_index,
            ])

        cmd.extend(["-c:v", encoder])
        if encoder == "libx264":
            cmd.extend(["-preset", preset, "-tune", "zerolatency"])
        elif encoder == "h264_nvenc":
            cmd.extend(["-preset", "p4", "-tune", "ll"])

        cmd.extend([
            "-b:v", video_bitrate,

            "-maxrate", max_rate,
            "-bufsize", buf_size,
            "-r", fps,
            "-g", gop_size,
            "-keyint_min", gop_size,
            "-sc_threshold", "0",
            "-pix_fmt", "yuv420p",
            "-c:a", audio_codec,
            "-b:a", audio_bitrate,
            "-ar", audio_sample_rate,
            "-ac", "2",
            "-af", "aresample=async=1",
            "-flvflags", "no_duration_filesize",
            "-f", "flv",
            destination_url,
        ])

        return cmd

    def build_news_command(
        self,
        video_path: str,
        audio_path: str,
        destination_url: str,
        banner_path: Optional[str] = "overlay/breaking_news.svg",
        profile_override: Optional[str] = None,
    ) -> List[str]:
        """Mode 6: 24/7 Live Breaking News Channel Studio with Lower-Third Ticker & Speech."""
        enc_params = self.resolve_quality_params(profile_override)
        overlay_cfg = self.config.get("overlay", {})

        resolution = enc_params["resolution"]
        fps = str(enc_params["fps"])
        preset = enc_params["preset"]
        video_bitrate = enc_params["video_bitrate"]
        max_rate = enc_params["max_rate"]
        buf_size = enc_params["buf_size"]
        gop_size = str(enc_params["gop_size"])
        threads = enc_params.get("threads", 0)

        audio_codec = enc_params.get("audio_codec", "aac")
        audio_bitrate = enc_params.get("audio_bitrate", "128k")
        audio_sample_rate = str(enc_params.get("audio_sample_rate", 44100))

        encoder = self.detect_encoder(self.config.get("encoding", {}).get("hw_accel", "auto"))

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel", "info",
            "-re",
        ]

        if threads > 0:
            cmd.extend(["-threads", str(threads)])

        cmd.extend(["-stream_loop", "-1", "-i", video_path])
        cmd.extend(["-i", audio_path])

        enable_overlay = overlay_cfg.get("enable", True)
        logo_path = overlay_cfg.get("logo_path", "logo/logo.svg")
        has_logo = enable_overlay and os.path.exists(logo_path)
        has_banner = banner_path and os.path.exists(banner_path)

        next_input_idx = 2
        logo_idx = None
        banner_idx = None

        if has_logo:
            cmd.extend(["-stream_loop", "-1", "-i", logo_path])
            logo_idx = next_input_idx
            next_input_idx += 1

        if has_banner:
            cmd.extend(["-stream_loop", "-1", "-i", banner_path])
            banner_idx = next_input_idx
            next_input_idx += 1

        res_w = int(resolution.split("x")[0]) if "x" in resolution else 1920
        news_banner_width = res_w - 40

        if logo_idx is not None or banner_idx is not None:
            filter_str = self.build_overlay_filter(
                logo_input_index=logo_idx,
                banner_input_index=banner_idx,
                resolution=resolution,
                scale_width=overlay_cfg.get("scale_width", 200),
                position=overlay_cfg.get("position", "top-right"),
                margin_x=overlay_cfg.get("margin_x", 24),
                margin_y=overlay_cfg.get("margin_y", 24),
                opacity=overlay_cfg.get("opacity", 0.92),
                max_allowed_logo_width=enc_params.get("max_logo_width", 200),
                banner_scale_width=res_w,
                banner_position="fullscreen",
            )
            cmd.extend(["-filter_complex", filter_str, "-map", "[outv]", "-map", "1:a"])
        else:
            res_colon = resolution.replace("x", ":")
            cmd.extend([
                "-vf", f"scale={res_colon},format=yuv420p",
                "-map", "0:v",
                "-map", "1:a",
            ])

        cmd.extend(["-c:v", encoder])
        if encoder == "libx264":
            cmd.extend(["-preset", preset, "-tune", "zerolatency"])
        elif encoder == "h264_nvenc":
            cmd.extend(["-preset", "p4", "-tune", "ll"])

        cmd.extend([
            "-b:v", video_bitrate,
            "-maxrate", max_rate,
            "-bufsize", buf_size,
            "-r", fps,
            "-g", gop_size,
            "-keyint_min", gop_size,
            "-sc_threshold", "0",
            "-pix_fmt", "yuv420p",
            "-c:a", audio_codec,
            "-b:a", audio_bitrate,
            "-ar", audio_sample_rate,
            "-ac", "2",
            "-af", "aresample=async=1",
            "-shortest",
            "-flvflags", "no_duration_filesize",
            "-f", "flv",
            destination_url,
        ])

        return cmd

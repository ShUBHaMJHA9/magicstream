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
        logo_input_index: int,
        resolution: str,
        scale_width: int = 200,
        position: str = "top-right",
        margin_x: int = 24,
        margin_y: int = 24,
        opacity: float = 0.92,
        max_allowed_logo_width: int = 200,
    ) -> str:
        """Builds a complex filter string for scaling, opacity, and positioning."""
        effective_width = min(scale_width, max_allowed_logo_width) if scale_width > 0 else max_allowed_logo_width

        pos = position.lower().strip()
        if pos == "top-left":
            coords = f"x={margin_x}:y={margin_y}"
        elif pos == "bottom-right":
            coords = f"x=W-w-{margin_x}:y=H-h-{margin_y}"
        elif pos == "bottom-left":
            coords = f"x={margin_x}:y=H-h-{margin_y}"
        elif pos == "center":
            coords = "x=(W-w)/2:y=(H-h)/2"
        else:
            coords = f"x=W-w-{margin_x}:y={margin_y}"

        scale_str = f"scale={effective_width}:-1" if effective_width > 0 else "null"
        alpha_str = f"colorchannelmixer=aa={opacity:.2f}"

        filter_str = (
            f"[{logo_input_index}:v]format=rgba,{scale_str},{alpha_str}[watermark];"
            f"[0:v]scale={resolution.replace('x', ':')},format=yuv420p[base];"
            f"[base][watermark]overlay={coords}[outv]"
        )
        return filter_str

    def build_radio_command(
        self,
        video_path: str,
        audio_url: str,
        destination_url: str,
        loop_video: bool = True,
        profile_override: Optional[str] = None,
    ) -> List[str]:
        """Mode 1 & Mode 3: Radio Looper / Custom Combiner with adaptive quality."""
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

        if has_logo:
            cmd.extend(["-stream_loop", "-1", "-i", logo_path])
            filter_str = self.build_overlay_filter(
                logo_input_index=2,
                resolution=resolution,
                scale_width=overlay_cfg.get("scale_width", 200),
                position=overlay_cfg.get("position", "top-right"),
                margin_x=overlay_cfg.get("margin_x", 24),
                margin_y=overlay_cfg.get("margin_y", 24),
                opacity=overlay_cfg.get("opacity", 0.92),
                max_allowed_logo_width=enc_params.get("max_logo_width", 200),
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

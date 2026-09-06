"""
Live Stream Lifecycle & 24/7 Resilience Manager for MagicStream
Author: Shubham Kumar Jha
License: MIT

Manages FFmpeg streaming execution, 24/7 auto-reconnection with backoff,
clean process termination, URL token refreshing, and adaptive quality auto-downgrade.
"""

import os
import re
import sys
import glob
import time
import signal
import random
import subprocess
import threading
from typing import Dict, Any, Optional, List
from collections import deque

from magicstream.config import ConfigManager
from magicstream.extractor import MediaExtractor
from magicstream.ffmpeg_builder import FFmpegBuilder
from magicstream.hardware import HardwareDetector, QUALITY_PROFILES


class LiveStreamManager:
    """Manages continuous 24/7 live streaming with adaptive auto-downgrade resilience."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.extractor = MediaExtractor(cookie_file=self.config_manager.get("streaming", {}).get("mode_2_yt_relay", {}).get("cookie_file", "cookies.txt"))
        self.ffmpeg_builder = FFmpegBuilder(self.config_manager.config)
        hw_accel = self.config_manager.get("encoding", {}).get("hw_accel", "auto")
        self.encoder = self.ffmpeg_builder.detect_encoder(hw_accel)

        # Process & state management
        self.active_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.stop_requested = False
        self.stream_thread: Optional[threading.Thread] = None

        # Adaptive Quality Management
        configured_profile = self.config_manager.get("encoding", {}).get("quality_profile", "auto")
        if configured_profile == "auto":
            self.active_profile_name = HardwareDetector.auto_detect_profile()
        else:
            self.active_profile_name = configured_profile

        self.auto_downgrade_enabled = self.config_manager.get("resilience", {}).get("auto_downgrade_on_lag", True)
        self.lag_counter = 0

        # Playback Selection Options: "sequential" or "random"
        self.playback_order = self.config_manager.get("streaming", {}).get("playback_order", "sequential")
        self.video_selection = self.config_manager.get("streaming", {}).get("video_selection", "random")
        self.current_track_index = 0
        self.total_tracks = 0

        # Telemetry & stats
        self.start_time: Optional[float] = None
        self.current_mode: str = self.config_manager.get("streaming", {}).get("mode", "mode_1_radio")
        self.current_media_title: str = "Idle"
        self.current_video_title: str = "vid.mp4"
        self.retry_count = 0
        self.recent_logs = deque(maxlen=100)
        self.silent_console: bool = False
        self.last_error_summary: Optional[str] = None

        # Logging & Diagnostics Configuration
        log_cfg = self.config_manager.get("logging", {})
        self.log_to_file: bool = log_cfg.get("enabled", True)
        self.log_file_path: str = log_cfg.get("file", "logs/stream.log")
        self.max_log_size_mb: int = log_cfg.get("max_size_mb", 10)
        self.backup_count: int = log_cfg.get("backup_count", 3)
        self.include_ffmpeg_raw: bool = log_cfg.get("include_ffmpeg_raw", True)
        self.log_lock = threading.Lock()

        if self.log_to_file and self.log_file_path:
            self._init_log_file()

        # Register OS signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _init_log_file(self) -> None:
        """Ensure log directory exists and write session header."""
        try:
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            self._rotate_log_if_needed()
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [MagicStream Session Started - v2.0.0]\n")
                f.write(f"  Author: Shubham Kumar Jha | Mode: {self.current_mode} | Profile: {self.active_profile_name}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            if not self.silent_console:
                print(f"[MagicStream Logger] Warning: Could not initialize log file '{self.log_file_path}': {e}")

    def _rotate_log_if_needed(self) -> None:
        """Rotate log file if size exceeds max_size_mb."""
        if not self.log_file_path or self.max_log_size_mb <= 0:
            return
        try:
            if os.path.exists(self.log_file_path):
                size_bytes = os.path.getsize(self.log_file_path)
                if size_bytes >= self.max_log_size_mb * 1024 * 1024:
                    for i in range(self.backup_count - 1, 0, -1):
                        s_fn = f"{self.log_file_path}.{i}"
                        d_fn = f"{self.log_file_path}.{i + 1}"
                        if os.path.exists(s_fn):
                            os.replace(s_fn, d_fn)
                    os.replace(self.log_file_path, f"{self.log_file_path}.1")
        except Exception:
            pass

    def log(self, message: str, level: str = "INFO") -> None:
        """Structured logging with timestamps, console output, in-memory buffer, and file persistence."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [MagicStream] [{level}] {message}"
        if not self.silent_console:
            print(formatted)
        self.recent_logs.append(formatted)

        if level in ("ERROR", "FATAL"):
            self.last_error_summary = message

        if self.log_to_file and self.log_file_path:
            with self.log_lock:
                try:
                    self._rotate_log_if_needed()
                    with open(self.log_file_path, "a", encoding="utf-8") as f:
                        f.write(formatted + "\n")
                        f.flush()
                except Exception:
                    pass

    def log_ffmpeg_output(self, line: str) -> None:
        """Log raw or filtered line from FFmpeg process directly to the log file."""
        if not self.log_to_file or not self.log_file_path or not self.include_ffmpeg_raw:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.log_lock:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [FFmpeg] {line}\n")
                    f.flush()
            except Exception:
                pass

    def _handle_signal(self, signum, frame):
        self.log(f"Received shutdown signal ({signum}). Terminating live stream cleanly...", level="WARNING")
        self.stop()
        sys.exit(0)

    def get_status(self) -> Dict[str, Any]:
        """Returns current operational status and hardware metrics."""
        uptime = int(time.time() - self.start_time) if self.is_running and self.start_time else 0
        dest_platform = self.config_manager.get("destination", {}).get("platform", "youtube")
        hw_summary = HardwareDetector.get_system_summary()

        return {
            "is_running": self.is_running,
            "mode": self.current_mode,
            "platform": dest_platform,
            "uptime_seconds": uptime,
            "uptime_formatted": f"{uptime // 3600:02d}:{(uptime % 3600) // 60:02d}:{uptime % 60:02d}",
            "current_media": self.current_media_title,
            "current_video": self.current_video_title,
            "playback_order": self.playback_order,
            "video_selection": self.video_selection,
            "current_track_index": self.current_track_index,
            "total_tracks": self.total_tracks,
            "active_profile": self.active_profile_name,
            "profile_info": QUALITY_PROFILES.get(self.active_profile_name, {}),
            "system_ram_mb": hw_summary["ram_mb"],
            "cpu_cores": hw_summary["cpu_cores"],
            "retries": self.retry_count,
            "pid": self.active_process.pid if self.active_process else None,
            "log_file": self.log_file_path if self.log_to_file else None,
            "last_error": self.last_error_summary,
        }


    def skip_track(self) -> bool:
        """Immediately skips the currently playing audio/video track."""
        if self.active_process:
            self.log("[Stream Control] User requested track skip. Advancing to next media...")
            try:
                self.active_process.terminate()
                return True
            except Exception as e:
                self.log(f"Error terminating process for track skip: {e}")
        return False

    def start(self, mode: Optional[str] = None, profile: Optional[str] = None) -> bool:
        """Starts streaming in a dedicated background worker thread."""
        if self.is_running:
            self.log("Stream is already running.")
            return False

        if mode:
            self.current_mode = mode
            self.config_manager.config["streaming"]["mode"] = mode

        if profile:
            self.active_profile_name = HardwareDetector.auto_detect_profile() if profile == "auto" else profile

        self.stop_requested = False
        self.is_running = True
        self.start_time = time.time()
        self.retry_count = 0
        self.lag_counter = 0

        self.stream_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.stream_thread.start()
        profile_label = QUALITY_PROFILES.get(self.active_profile_name, {}).get("name", self.active_profile_name)
        self.log(f"Started live streaming worker: Mode={self.current_mode} | Profile={profile_label}")
        return True

    def stop(self) -> bool:
        """Stops active FFmpeg process immediately."""
        if not self.is_running and not self.active_process:
            self.log("Stream is not currently running.")
            return False

        self.log("Stopping live stream...")
        self.stop_requested = True
        self.is_running = False

        proc = self.active_process
        self.active_process = None
        if proc:
            try:
                if proc.stdin and not proc.stdin.closed:
                    try:
                        proc.stdin.write(b"q\n")
                        proc.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        self.current_media_title = "Stopped"
        self.log("Live stream stopped successfully.")
        return True

    def _execute_ffmpeg(self, cmd: List[str]) -> int:
        """Executes FFmpeg with real-time speed monitoring, raw logging, and auto-downgrade triggers."""
        # Sanitize sensitive stream key in logged command
        safe_cmd = []
        for token in cmd:
            if "rtmp://" in token or "rtmps://" in token:
                parts = token.rsplit("/", 1)
                if len(parts) == 2 and len(parts[1]) > 4:
                    safe_cmd.append(f"{parts[0]}/***REDACTED***")
                else:
                    safe_cmd.append(token)
            else:
                safe_cmd.append(token)

        cmd_summary = " ".join(safe_cmd[:7])
        self.log(f"Spawning FFmpeg process: {cmd_summary} ...")
        if self.log_to_file and self.log_file_path:
            with self.log_lock:
                try:
                    with open(self.log_file_path, "a", encoding="utf-8") as f:
                        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [FFmpeg CMD] {' '.join(safe_cmd)}\n")
                        f.flush()
                except Exception:
                    pass

        last_ffmpeg_lines = deque(maxlen=40)
        try:
            self.active_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            speed_pattern = re.compile(r"speed=\s*([0-9\.]+)x")

            for line in iter(self.active_process.stdout.readline, ""):
                if self.stop_requested:
                    break
                stripped = line.strip()
                if stripped:
                    last_ffmpeg_lines.append(stripped)
                    self.log_ffmpeg_output(stripped)
                    if "speed=" in stripped:
                        self.recent_logs.append(f"[FFmpeg] {stripped}")
                        match = speed_pattern.search(stripped)
                        if match and self.auto_downgrade_enabled:
                            try:
                                speed_val = float(match.group(1))
                                if speed_val < 0.85:
                                    self.lag_counter += 1
                                    if self.lag_counter >= 5:
                                        self.log(f"[Adaptive Watchdog] Encoding speed is lagging ({speed_val:.2f}x < 1.0x).", level="WARNING")
                                        self._trigger_auto_downgrade()
                                        break
                                else:
                                    self.lag_counter = max(0, self.lag_counter - 1)
                            except ValueError:
                                pass
                    elif any(err_kw in stripped.lower() for err_kw in ("error", "fatal", "failed", "broken pipe", "connection refused", "invalid")):
                        self.log(f"[FFmpeg Alert] {stripped}", level="WARNING")

            proc = self.active_process
            returncode = 0
            if proc:
                try:
                    returncode = proc.wait(timeout=5)
                except Exception:
                    returncode = -1
            if returncode != 0 and not self.stop_requested:
                error_summary = "\n  ".join(list(last_ffmpeg_lines)[-15:])
                diag_msg = (
                    f"FFmpeg exited abnormally with return code {returncode}!\n"
                    f"--- Last FFmpeg Error Output ---\n  {error_summary}\n"
                    f"--- Check full log file: {self.log_file_path} ---"
                )
                self.log(diag_msg, level="ERROR")
            return returncode
        except Exception as e:
            if not self.stop_requested:
                self.log(f"FFmpeg execution error: {e}", level="ERROR")
            return -1
        finally:
            self.active_process = None


    def _trigger_auto_downgrade(self) -> None:
        """Downgrades video quality profile to a lower tier to prevent stream crashes."""
        lower_profile = HardwareDetector.get_downgraded_profile_name(self.active_profile_name)
        if lower_profile != self.active_profile_name:
            self.log(f"[Adaptive Engine] Downgrading quality: '{self.active_profile_name}' -> '{lower_profile}' to eliminate lag.")
            self.active_profile_name = lower_profile
            self.lag_counter = 0
            if self.active_process:
                try:
                    self.active_process.terminate()
                    self.active_process.wait(timeout=3)
                except Exception:
                    try:
                        self.active_process.kill()
                    except Exception:
                        pass

    def _run_loop(self) -> None:
        """Main 24/7 resilience loop."""
        resilience_cfg = self.config_manager.get("resilience", {})
        auto_reconnect = resilience_cfg.get("auto_reconnect", True)
        max_retries = resilience_cfg.get("max_retries", 50)
        base_delay = resilience_cfg.get("retry_delay_sec", 5)
        backoff_factor = resilience_cfg.get("backoff_factor", 1.2)
        max_delay = resilience_cfg.get("max_retry_delay_sec", 60)

        while not self.stop_requested and self.is_running:
            try:
                destination_url = self.config_manager.get_destination_url()
            except Exception as e:
                self.log(f"Configuration Error: {e}")
                self.stop()
                break

            try:
                if self.current_mode == "mode_1_radio":
                    self._stream_mode_1_radio(destination_url)
                elif self.current_mode == "mode_2_yt_relay":
                    self._stream_mode_2_yt_relay(destination_url)
                elif self.current_mode == "mode_3_custom":
                    self._stream_mode_3_custom(destination_url)
                elif self.current_mode == "mode_4_local_playlist":
                    self._stream_mode_4_local_playlist(destination_url)
                elif self.current_mode == "mode_5_direct_relay":
                    self._stream_mode_5_direct_relay(destination_url)
                else:
                    self.log(f"Unknown streaming mode: {self.current_mode}")
                    self.stop()
                    break

            except Exception as e:
                self.log(f"Stream runtime exception: {e}", level="ERROR")

            if self.stop_requested:
                break

            if not auto_reconnect or self.retry_count >= max_retries:
                self.log(f"Auto-reconnect threshold reached ({self.retry_count}/{max_retries}). Halting.", level="WARNING")
                self.stop()
                break

            self.retry_count += 1
            delay = min(base_delay * (backoff_factor ** (self.retry_count - 1)), max_delay)
            self.log(f"Stream interrupted. Reconnecting in {delay:.1f}s (Attempt {self.retry_count}/{max_retries})...", level="WARNING")
            time.sleep(delay)


    # --------------------------------------------------------------------------
    # MODES
    # --------------------------------------------------------------------------
    def _stream_mode_1_radio(self, destination_url: str) -> None:
        """Mode 1: Looping Video + YouTube Audio Stream / Playlist with Adaptive Quality."""
        mode_cfg = self.config_manager.get("streaming", {}).get("mode_1_radio", {})
        video_path = mode_cfg.get("video_path", "video/vid.mp4")
        audio_source = mode_cfg.get("audio_source", "audio/audio.txt")

        video_files = []
        if os.path.isdir("video"):
            for ext in ("*.mp4", "*.mkv", "*.mov", "*.webm"):
                video_files.extend(glob.glob(os.path.join("video", ext)))
        if not video_files:
            if video_path.startswith(("http://", "https://")):
                video_files = [video_path]
            elif os.path.exists(video_path):
                video_files = [video_path]
            elif os.path.exists("vid.mp4"):
                video_files = ["vid.mp4"]

        if not video_files:
            self.log("Error: No background video files found in video/ or root.", level="ERROR")
            time.sleep(5)
            return

        audio_items = []
        if os.path.isfile(audio_source):
            audio_items = self.extractor.parse_playlist_file(audio_source)
        elif audio_source.startswith("http"):
            audio_items = [audio_source]

        if not audio_items and os.path.exists("audio.txt"):
            audio_items = self.extractor.parse_playlist_file("audio.txt")

        if not audio_items:
            self.log("Error: No audio sources found to play.", level="ERROR")
            time.sleep(5)
            return

        items_to_play = list(audio_items)
        if self.playback_order == "random":
            random.shuffle(items_to_play)

        self.total_tracks = len(items_to_play)

        for idx, audio_item in enumerate(items_to_play):
            if self.stop_requested:
                break

            self.current_track_index = idx + 1

            if self.video_selection == "random":
                active_video = random.choice(video_files)
            else:
                active_video = video_files[idx % len(video_files)]

            # If background video is a YouTube or remote URL, extract direct video stream
            active_video_resolved = active_video
            if active_video.startswith(("http://", "https://")):
                self.log(f"Resolving direct video stream URL from: {active_video}")
                v_data = self.extractor.extract_video_stream(active_video, quality="best", force_refresh=(self.retry_count > 0))
                if v_data and v_data.get("video_url"):
                    active_video_resolved = v_data["video_url"]
                    self.current_video_title = v_data.get("title", active_video)
                else:
                    err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
                    self.log(f"Failed to extract video stream from {active_video}. Error: {err_detail}", level="ERROR")
                    time.sleep(5)
                    continue
            else:
                self.current_video_title = os.path.basename(active_video)

            self.log(f"Resolving audio stream [{self.current_track_index}/{self.total_tracks}]: {audio_item} | Video: {self.current_video_title}")

            audio_stream_url = self.extractor.extract_audio_url(audio_item, force_refresh=(self.retry_count > 0))
            if not audio_stream_url:
                err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
                self.log(f"Could not extract audio for {audio_item}. Error: {err_detail}. Skipping to next track...", level="ERROR")
                continue

            self.current_media_title = audio_item
            cmd = self.ffmpeg_builder.build_radio_command(
                video_path=active_video_resolved,
                audio_url=audio_stream_url,
                destination_url=destination_url,
                loop_video=True,
                profile_override=self.active_profile_name,
            )
            self._execute_ffmpeg(cmd)


    def _stream_mode_2_yt_relay(self, destination_url: str) -> None:
        """Mode 2: Relay YouTube stream or video with adaptive quality."""
        mode_cfg = self.config_manager.get("streaming", {}).get("mode_2_yt_relay", {})
        yt_source_url = mode_cfg.get("youtube_source_url")
        quality = mode_cfg.get("quality", "best")

        if not yt_source_url:
            self.log("Error: No YouTube source URL specified for Mode 2.", level="ERROR")
            time.sleep(5)
            return

        self.log(f"Extracting YouTube live/video stream from: {yt_source_url}")
        stream_data = self.extractor.extract_video_stream(yt_source_url, quality=quality, force_refresh=(self.retry_count > 0))
        if not stream_data or not stream_data.get("video_url"):
            err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
            self.log(f"Failed to extract video stream from {yt_source_url}. Error: {err_detail}", level="ERROR")
            time.sleep(5)
            return


        self.current_media_title = stream_data.get("title", yt_source_url)
        cmd = self.ffmpeg_builder.build_relay_command(
            video_source_url=stream_data["video_url"],
            audio_source_url=stream_data.get("audio_url"),
            destination_url=destination_url,
            is_live=stream_data.get("is_live", True),
            profile_override=self.active_profile_name,
        )
        self._execute_ffmpeg(cmd)

    def _stream_mode_3_custom(self, destination_url: str) -> None:
        """Mode 3: Custom Video Link/File + Custom Audio Link/File."""
        mode_cfg = self.config_manager.get("streaming", {}).get("mode_3_custom", {})
        video_source = mode_cfg.get("video_source", "video/vid.mp4")
        audio_source = mode_cfg.get("audio_source", "audio/audio.txt")

        # Resolve Video Source: can be a local video file OR a YouTube/remote video URL
        resolved_video_url = video_source
        if video_source.startswith(("http://", "https://")):
            self.log(f"[Mode 3] Resolving direct video stream URL from: {video_source}")
            v_data = self.extractor.extract_video_stream(video_source, quality="best", force_refresh=(self.retry_count > 0))
            if v_data and v_data.get("video_url"):
                resolved_video_url = v_data["video_url"]
                self.current_video_title = v_data.get("title", video_source)
                self.log(f"[Mode 3] Extracted direct video stream URL (no download): {self.current_video_title}")
            else:
                err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
                self.log(f"[Mode 3] Failed to extract video stream from {video_source}. Error: {err_detail}", level="ERROR")
                time.sleep(5)
                return
        else:
            if not os.path.exists(video_source) and os.path.exists("vid.mp4"):
                resolved_video_url = "vid.mp4"
            self.current_video_title = os.path.basename(resolved_video_url)

        # Resolve Audio Source: can be playlist file, local audio file, or YouTube/web URL
        if os.path.isfile(audio_source):
            items = self.extractor.parse_playlist_file(audio_source)
            target_audio = items[0] if items else ""
        else:
            target_audio = audio_source

        self.log(f"[Mode 3] Resolving direct audio stream URL from: {target_audio}")
        resolved_audio_url = self.extractor.extract_audio_url(target_audio, force_refresh=(self.retry_count > 0))
        if not resolved_audio_url:
            err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
            self.log(f"[Mode 3] Could not resolve audio for {target_audio}. Error: {err_detail}", level="ERROR")
            time.sleep(5)
            return

        self.current_media_title = f"{self.current_video_title} + {target_audio}"
        cmd = self.ffmpeg_builder.build_radio_command(
            video_path=resolved_video_url,
            audio_url=resolved_audio_url,
            destination_url=destination_url,
            loop_video=mode_cfg.get("loop_video", True),
            profile_override=self.active_profile_name,
        )
        self._execute_ffmpeg(cmd)


    def _stream_mode_4_local_playlist(self, destination_url: str) -> None:
        """Mode 4: Continuous 24/7 loop of local video/audio files."""
        mode_cfg = self.config_manager.get("streaming", {}).get("mode_4_local_playlist", {})
        video_dir = mode_cfg.get("video_dir", "video")
        audio_dir = mode_cfg.get("audio_dir", "audio")

        video_files = []
        for ext in ("*.mp4", "*.mkv", "*.mov", "*.webm"):
            video_files.extend(glob.glob(os.path.join(video_dir, ext)))
        if not video_files and os.path.exists("vid.mp4"):
            video_files = ["vid.mp4"]

        audio_files = []
        for ext in ("*.mp3", "*.wav", "*.aac", "*.flac", "*.m4a"):
            audio_files.extend(glob.glob(os.path.join(audio_dir, ext)))

        if not video_files:
            self.log("Error: No local video files found in video/ directory.", level="ERROR")
            time.sleep(5)
            return

        if not audio_files:
            audio_txt = os.path.join(audio_dir, "audio.txt")
            if os.path.exists(audio_txt):
                audio_files = self.extractor.parse_playlist_file(audio_txt)
            elif os.path.exists("audio.txt"):
                audio_files = self.extractor.parse_playlist_file("audio.txt")

        if not audio_files:
            self.log("Error: No audio files or playlists found.", level="ERROR")
            time.sleep(5)
            return


        if mode_cfg.get("shuffle", False):
            random.shuffle(audio_files)

        for audio_item in audio_files:
            if self.stop_requested:
                break
            bg_video = random.choice(video_files)
            resolved_audio = self.extractor.extract_audio_url(audio_item)
            if not resolved_audio:
                continue

            self.current_media_title = f"{os.path.basename(bg_video)} + {os.path.basename(audio_item)}"
            cmd = self.ffmpeg_builder.build_radio_command(
                video_path=bg_video,
                audio_url=resolved_audio,
                destination_url=destination_url,
                loop_video=True,
                profile_override=self.active_profile_name,
            )
            self._execute_ffmpeg(cmd)

    def _stream_mode_5_direct_relay(self, destination_url: str) -> None:
        """Mode 5: Direct HLS / RTMP / RTSP or YouTube stream relay."""
        mode_cfg = self.config_manager.get("streaming", {}).get("mode_5_direct_relay", {})
        input_url = mode_cfg.get("input_stream_url")

        if not input_url:
            self.log("Error: No input_stream_url configured for Mode 5.", level="ERROR")
            time.sleep(5)
            return

        resolved_stream_url = input_url
        video_title = input_url

        if "youtube.com" in input_url or "youtu.be" in input_url:
            self.log(f"[Mode 5] Extracting direct streaming URL for YouTube link: {input_url}")
            stream_data = self.extractor.extract_video_stream(input_url, quality="best", force_refresh=(self.retry_count > 0))
            if stream_data and stream_data.get("video_url"):
                resolved_stream_url = stream_data["video_url"]
                video_title = stream_data.get("title", input_url)
                self.log(f"[Mode 5] Extracted direct streaming URL (no download): {video_title}")
            else:
                err_detail = self.extractor.last_error or "yt-dlp returned no stream URL"
                self.log(f"[Mode 5] Failed to extract stream URL from {input_url}. Error: {err_detail}", level="ERROR")
                time.sleep(5)
                return

        self.current_media_title = f"Direct Stream: {video_title}"
        cmd = self.ffmpeg_builder.build_relay_command(
            video_source_url=resolved_stream_url,
            audio_source_url=None,
            destination_url=destination_url,
            is_live=True,
            profile_override=self.active_profile_name,
        )
        self._execute_ffmpeg(cmd)


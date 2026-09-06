"""
Configuration Management Module for MagicStream
Author: Shubham Kumar Jha
License: MIT

Handles loading configuration from config.yaml, environment variables,
and runtime overrides for multi-platform streaming.
"""

import os
from typing import Dict, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "destination": {
        "platform": "youtube",
        "stream_key": "",
        "custom_rtmp_url": "",
        "endpoints": {
            "youtube": "rtmp://a.rtmp.youtube.com/live2/{stream_key}",
            "youtube_backup": "rtmp://b.rtmp.youtube.com/live2?backup=1/{stream_key}",
            "facebook": "rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}",
            "twitch": "rtmp://live.twitch.tv/app/{stream_key}",
            "kick": "rtmps://fa723fc1b171.global-contribute.live-video.net:443/app/{stream_key}",
        },
    },
    "streaming": {
        "mode": "mode_1_radio",
        "playback_order": "random",
        "video_selection": "random",
        "mode_1_radio": {
            "video_path": "video/vid.mp4",
            "audio_source": "audio/audio.txt",
            "shuffle": True,
            "loop_continuous": True,
        },
        "mode_2_yt_relay": {
            "youtube_source_url": "",
            "stream_live_source": True,
            "quality": "best",
            "cookie_file": "cookies.txt",
        },
        "mode_3_custom": {
            "video_source": "video/vid.mp4",
            "audio_source": "audio/audio.txt",
            "loop_video": True,
        },
        "mode_4_local_playlist": {
            "video_dir": "video",
            "audio_dir": "audio",
            "shuffle": True,
            "continuous_loop": True,
        },
        "mode_5_direct_relay": {
            "input_stream_url": "",
            "re_encode": True,
        },
        "mode_6_news": {
            "category": "world",
            "language": "en",
            "tts_enabled": True,
            "ambient_audio": "audio/news_ambient.mp3",
            "video_path": "video/vid.mp4",
        },
    },
    "overlay": {
        "enable": True,
        "logo_path": "logo/logo.svg",
        "position": "top-right",
        "margin_x": 24,
        "margin_y": 24,
        "scale_width": 200,
        "opacity": 0.92,
        "now_playing": {
            "enable": True,
            "channel_name": "MAGICSTREAM LIVE",
            "position": "bottom-left",
        },
    },
    "encoding": {
        "quality_profile": "auto",
        "hw_accel": "auto",
    },
    "resilience": {
        "auto_reconnect": True,
        "auto_downgrade_on_lag": True,
        "max_retries": 50,
        "retry_delay_sec": 5,
        "backoff_factor": 1.2,
        "max_retry_delay_sec": 60,
        "refresh_url_on_retry": True,
    },
    "api": {
        "enabled": True,
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "info",
    },
    "logging": {
        "enabled": True,
        "file": "logs/stream.log",
        "level": "INFO",
        "max_size_mb": 10,
        "backup_count": 3,
        "include_ffmpeg_raw": True,
    },
}



class ConfigManager:
    """Centralized configuration loader with priority: CLI > Env > YAML > Defaults."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = self._deep_copy(DEFAULT_CONFIG)
        self.load()

    def _deep_copy(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._deep_copy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy(v) for v in data]
        return data

    def _merge_dict(self, base: dict, override: dict) -> dict:
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._merge_dict(base[k], v)
            else:
                base[k] = v
        return base

    def load(self) -> None:
        """Load YAML and overlay environment variables."""
        if os.path.exists(self.config_path) and yaml is not None:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_data = yaml.safe_load(f)
                    if isinstance(file_data, dict):
                        self.config = self._merge_dict(self.config, file_data)
            except Exception as e:
                print(f"[MagicStream Config] Warning: Could not parse {self.config_path}: {e}")

        # Environment Variables Overrides
        env_platform = os.getenv("STREAM_PLATFORM")
        if env_platform:
            self.config["destination"]["platform"] = env_platform.lower()

        env_stream_key = os.getenv("STREAM_KEY") or os.getenv("YOUTUBE_STREAM_KEY")
        if env_stream_key:
            self.config["destination"]["stream_key"] = env_stream_key

        env_fb_key = os.getenv("FB_STREAM_KEY")
        if env_fb_key and self.config["destination"]["platform"] == "facebook":
            self.config["destination"]["stream_key"] = env_fb_key

        env_custom_rtmp = os.getenv("CUSTOM_RTMP_URL")
        if env_custom_rtmp:
            self.config["destination"]["custom_rtmp_url"] = env_custom_rtmp

        env_mode = os.getenv("STREAM_MODE")
        if env_mode:
            self.config["streaming"]["mode"] = env_mode

        env_video = os.getenv("VIDEO_PATH")
        if env_video:
            self.config["streaming"]["mode_1_radio"]["video_path"] = env_video
            self.config["streaming"]["mode_3_custom"]["video_source"] = env_video

        env_audio = os.getenv("AUDIO_SOURCE")
        if env_audio:
            self.config["streaming"]["mode_1_radio"]["audio_source"] = env_audio
            self.config["streaming"]["mode_3_custom"]["audio_source"] = env_audio

        env_logo = os.getenv("LOGO_PATH")
        if env_logo:
            self.config["overlay"]["logo_path"] = env_logo

        env_logo_pos = os.getenv("LOGO_POSITION")
        if env_logo_pos:
            self.config["overlay"]["position"] = env_logo_pos

        env_hw_accel = os.getenv("HW_ACCEL")
        if env_hw_accel:
            self.config["encoding"]["hw_accel"] = env_hw_accel

        env_port = os.getenv("PORT")
        if env_port:
            try:
                self.config["api"]["port"] = int(env_port)
            except ValueError:
                pass

        env_log_file = os.getenv("STREAM_LOG_FILE") or os.getenv("LOG_FILE")
        if env_log_file:
            self.config["logging"]["file"] = env_log_file


    def get_destination_url(self, platform_override: Optional[str] = None, stream_key_override: Optional[str] = None) -> str:
        """
        Builds the destination RTMP/RTMPS URL based on platform and stream key.
        Supports YouTube, Facebook, Twitch, Kick, and custom RTMP destinations.
        """
        dest = self.config.get("destination", {})
        platform = (platform_override or dest.get("platform", "youtube")).lower()
        stream_key = stream_key_override or dest.get("stream_key", "")
        custom_url = dest.get("custom_rtmp_url", "").strip()

        if custom_url and (platform == "custom" or not stream_key):
            if "{stream_key}" in custom_url:
                return custom_url.format(stream_key=stream_key)
            return custom_url

        if stream_key and (stream_key.startswith("rtmp://") or stream_key.startswith("rtmps://")):
            return stream_key

        endpoints = dest.get("endpoints", DEFAULT_CONFIG["destination"]["endpoints"])
        template = endpoints.get(platform, endpoints.get("youtube"))

        if not stream_key:
            raise ValueError(f"No stream key provided for platform '{platform}'. Set STREAM_KEY in config.yaml or .env")

        return template.format(stream_key=stream_key)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

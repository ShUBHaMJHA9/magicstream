"""
================================================================================
MagicStream: Professional 24/7 Multi-Platform Live Broadcast Engine
Author: Shubham Kumar Jha
License: MIT
================================================================================
A modular, publishing-ready Python package for 24/7 live streaming to YouTube,
Facebook Live, Twitch, Kick, and custom RTMP destinations with real-time
adaptive hardware quality profiling and watermark overlays.
"""

from magicstream.config import ConfigManager
from magicstream.hardware import HardwareDetector, QUALITY_PROFILES
from magicstream.extractor import MediaExtractor
from magicstream.ffmpeg_builder import FFmpegBuilder
from magicstream.streamer import LiveStreamManager
from magicstream.api import create_api_app
from magicstream.ui import get_banner, render_hardware_card, render_box_top, render_box_line, render_box_bottom

__version__ = "2.0.0"
__author__ = "Shubham Kumar Jha"
__license__ = "MIT"

__all__ = [
    "ConfigManager",
    "HardwareDetector",
    "QUALITY_PROFILES",
    "MediaExtractor",
    "FFmpegBuilder",
    "LiveStreamManager",
    "create_api_app",
    "get_banner",
    "render_hardware_card",
    "render_box_top",
    "render_box_line",
    "render_box_bottom",
    "__version__",
    "__author__",
    "__license__",
]

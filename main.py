#!/usr/bin/env python3
"""
================================================================================
YT_LIVE: Professional Multi-Platform 24/7 Live Streaming Engine
Author: Shubham Kumar Jha
License: MIT
Repository: https://github.com/shubhamkumarjha/YT_LIVE
================================================================================
"""

import os
import sys
import argparse
import threading
import time
from typing import Optional

from core.config import ConfigManager
from core.streamer import LiveStreamManager
from core.hardware import HardwareDetector, QUALITY_PROFILES
from core.api import create_api_app

try:
    import uvicorn
except ImportError:
    uvicorn = None


BANNER = r"""
 __   _______ _     _____ _    _ _____ 
 \ \ / /_   _| |   |_   _| |  | |  ___|
  \ V /  | | | |     | | | |  | | |__  
   | |   | | | |     | | | |/\| |  __| 
   | |   | | | |____ _| |_\  /\  / |___ 
   |_|   \_/ \_____/|____/ \/  \/\____/ 
 
 >> Professional Multi-Platform 24/7 Live Broadcast Engine
 >> Author: Shubham Kumar Jha | License: MIT
================================================================================
"""


def parse_arguments():
    """Parse command-line arguments for automated or headless execution."""
    parser = argparse.ArgumentParser(
        description="YT_LIVE: Professional 24/7 Live Streaming Engine for YouTube, Facebook, Twitch & Custom RTMP.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["1", "2", "3", "4", "5", "mode_1_radio", "mode_2_yt_relay", "mode_3_custom", "mode_4_local_playlist", "mode_5_direct_relay"],
        default=None,
        help=(
            "Streaming Mode Selection:\n"
            "  1 / mode_1_radio         : Looping video + YouTube audio playlist\n"
            "  2 / mode_2_yt_relay      : Restream YouTube live stream or video\n"
            "  3 / mode_3_custom        : Custom video link/file + custom audio\n"
            "  4 / mode_4_local_playlist: Continuous 24/7 loop of local video/audio files\n"
            "  5 / mode_5_direct_relay  : Direct HLS/m3u8/RTMP stream restreamer"
        )
    )

    parser.add_argument(
        "--platform", "-p",
        choices=["youtube", "facebook", "twitch", "kick", "custom"],
        default=None,
        help="Streaming destination platform (default: youtube or config.yaml value)"
    )

    parser.add_argument(
        "--stream-key", "-k",
        default=None,
        help="Target stream key (overrides config.yaml and environment variables)"
    )

    parser.add_argument(
        "--custom-rtmp",
        default=None,
        help="Custom RTMP/RTMPS destination URL (e.g. rtmps://live-api-s.facebook.com:443/rtmp/<key>)"
    )

    parser.add_argument(
        "--video", "-v",
        default=None,
        help="Path or URL to video source (default: video/vid.mp4 or vid.mp4)"
    )

    parser.add_argument(
        "--audio", "-a",
        default=None,
        help="Path to audio file/playlist or YouTube URL (default: audio/audio.txt)"
    )

    parser.add_argument(
        "--yt-source",
        default=None,
        help="YouTube source URL for Mode 2 (Relay / Restream)"
    )

    parser.add_argument(
        "--quality", "-q",
        choices=["auto", "ultra_low", "low", "medium", "high"],
        default=None,
        help=(
            "Quality Profile:\n"
            "  auto      : Auto-detect machine RAM/CPU/containers (512MB RAM to 16-core servers)\n"
            "  ultra_low : 240p @ 15fps, 250k bitrate (500MB-1GB RAM, 0.1-0.5 vCPU containers)\n"
            "  low       : 480p @ 24fps, 800k bitrate (1GB-2GB RAM, 1 vCPU)\n"
            "  medium    : 720p @ 30fps, 2500k bitrate (2GB-4GB RAM, 2 vCPUs)\n"
            "  high      : 1080p @ 30fps, 4500k bitrate (4GB+ RAM, 4+ vCPUs or GPU)"
        )
    )

    parser.add_argument(
        "--logo",
        default=None,
        help="Path to watermark logo (.svg, .png, .jpg). Default: logo/logo.svg"
    )

    parser.add_argument(
        "--logo-pos",
        choices=["top-right", "top-left", "bottom-right", "bottom-left", "center"],
        default=None,
        help="Watermark position on screen (default: top-right)"
    )

    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Disable watermark logo overlay on the stream"
    )

    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Start only the FastAPI web dashboard and API server without auto-starting stream"
    )

    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Run stream in pure CLI mode without launching the FastAPI server"
    )

    parser.add_argument(
        "--terminal", "-t",
        action="store_true",
        help="Launch the colorful animated terminal broadcast studio and controller"
    )

    parser.add_argument(
        "--playback-order",
        choices=["sequential", "random"],
        default=None,
        help="Audio playback order: 'sequential' (loop 1 by 1) or 'random' (shuffle)"
    )

    parser.add_argument(
        "--video-selection",
        choices=["single", "sequential", "random"],
        default=None,
        help="Video selection style: 'single', 'sequential', or 'random' from video/ folder"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Web API / Dashboard port (default: 8000)"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Launch interactive terminal wizard menu"
    )

    return parser.parse_args()


def normalize_mode(mode_arg: Optional[str]) -> Optional[str]:
    """Map numeric mode flags ('1', '2', etc.) to full mode keys."""
    if not mode_arg:
        return None
    mode_map = {
        "1": "mode_1_radio",
        "2": "mode_2_yt_relay",
        "3": "mode_3_custom",
        "4": "mode_4_local_playlist",
        "5": "mode_5_direct_relay",
    }
    return mode_map.get(mode_arg, mode_arg)


def run_interactive_menu(config_manager: ConfigManager, streamer: LiveStreamManager):
    """Rich interactive terminal menu wizard."""
    hw = HardwareDetector.get_system_summary()

    print(BANNER)
    print(f" Detected System Resources: {hw['ram_mb']} MB RAM | {hw['cpu_cores']} vCPU Cores")
    print(f" Recommended Quality Profile: {hw['profile_name']}")
    print("-" * 80)
    print(" Select an option:")
    print("  [T] Launch Vibrant Terminal Studio & Live Controller (Made with ❤️ by Shubham Kumar Jha)")
    print("  [1] Mode 1: Radio Looper (Looping video + YouTube audio playlist)")
    print("  [2] Mode 2: YouTube Relay (Restream YouTube live stream / video to target)")
    print("  [3] Mode 3: Custom Media (Custom video URL/file + Custom audio URL/file)")
    print("  [4] Mode 4: Local Playlist 24/7 (Continuous folder-based loop)")
    print("  [5] Mode 5: Direct Stream Relay (HLS/m3u8/RTMP to target)")
    print("  [6] Web Dashboard & API Server Only")
    print("  [7] Hardware & Resource Capability Report")
    print("  [0] Exit")
    print("-" * 80)

    try:
        choice = input("Enter choice [T, 1-7, 0]: ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        sys.exit(0)

    if choice == "T":
        import runner
        runner.main()
        sys.exit(0)
    elif choice == "1":
        return "mode_1_radio", False
    elif choice == "2":
        yt_url = input("Enter YouTube Source Video or Live URL: ").strip()
        if yt_url:
            config_manager.config["streaming"]["mode_2_yt_relay"]["youtube_source_url"] = yt_url
        return "mode_2_yt_relay", False
    elif choice == "3":
        video_src = input("Enter Video Source (default: video/vid.mp4): ").strip()
        audio_src = input("Enter Audio Source (URL or audio/audio.txt): ").strip()
        if video_src:
            config_manager.config["streaming"]["mode_3_custom"]["video_source"] = video_src
        if audio_src:
            config_manager.config["streaming"]["mode_3_custom"]["audio_source"] = audio_src
        return "mode_3_custom", False
    elif choice == "4":
        return "mode_4_local_playlist", False
    elif choice == "5":
        stream_url = input("Enter HLS/m3u8/RTMP Stream URL: ").strip()
        if stream_url:
            config_manager.config["streaming"]["mode_5_direct_relay"]["input_stream_url"] = stream_url
        return "mode_5_direct_relay", False
    elif choice == "6":
        return None, True
    elif choice == "7":
        print("\n--- Hardware Resource Profile ---")
        for k, v in hw.items():
            print(f"  {k}: {v}")
        print("-" * 40)
        input("Press Enter to return...")
        return run_interactive_menu(config_manager, streamer)
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice, defaulting to Mode 1 (Radio Looper).")
        return "mode_1_radio", False


def main():
    args = parse_arguments()
    config_manager = ConfigManager()

    # Apply CLI Overrides
    if args.platform:
        config_manager.config["destination"]["platform"] = args.platform
    if args.stream_key:
        config_manager.config["destination"]["stream_key"] = args.stream_key
    if args.custom_rtmp:
        config_manager.config["destination"]["custom_rtmp_url"] = args.custom_rtmp

    selected_mode = normalize_mode(args.mode)
    if selected_mode:
        config_manager.config["streaming"]["mode"] = selected_mode

    if args.video:
        config_manager.config["streaming"]["mode_1_radio"]["video_path"] = args.video
        config_manager.config["streaming"]["mode_3_custom"]["video_source"] = args.video
    if args.audio:
        config_manager.config["streaming"]["mode_1_radio"]["audio_source"] = args.audio
        config_manager.config["streaming"]["mode_3_custom"]["audio_source"] = args.audio
    if args.yt_source:
        config_manager.config["streaming"]["mode_2_yt_relay"]["youtube_source_url"] = args.yt_source

    if args.quality:
        config_manager.config["encoding"]["quality_profile"] = args.quality

    if args.logo:
        config_manager.config["overlay"]["logo_path"] = args.logo
    if args.logo_pos:
        config_manager.config["overlay"]["position"] = args.logo_pos
    if args.no_overlay:
        config_manager.config["overlay"]["enable"] = False

    if args.playback_order:
        config_manager.config["streaming"]["playback_order"] = args.playback_order
    if args.video_selection:
        config_manager.config["streaming"]["video_selection"] = args.video_selection

    if args.terminal:
        import runner
        runner.main()
        return

    port = args.port or config_manager.get("api", {}).get("port", 8000)

    # Initialize Stream Manager
    streamer = LiveStreamManager(config_manager)
    streamer.playback_order = config_manager.config["streaming"].get("playback_order", "random")
    streamer.video_selection = config_manager.config["streaming"].get("video_selection", "random")

    # Interactive Wizard Mode (if explicitly requested or if no arguments provided and running in a TTY)
    api_only = args.api_only
    if args.interactive or (len(sys.argv) == 1 and sys.stdin.isatty()):
        interactive_mode, api_only = run_interactive_menu(config_manager, streamer)
        if interactive_mode:
            config_manager.config["streaming"]["mode"] = interactive_mode

    target_mode = config_manager.get("streaming", {}).get("mode", "mode_1_radio")
    platform = config_manager.get("destination", {}).get("platform", "youtube")

    print(BANNER)
    hw = HardwareDetector.get_system_summary()
    print(f"[System] Detected RAM: {hw['ram_mb']} MB | CPU Cores: {hw['cpu_cores']}")
    print(f"[Engine] Mode: {target_mode} | Destination: {platform.upper()} | Profile: {streamer.active_profile_name}")

    # Launch Stream Worker Thread unless api_only is set
    if not api_only:
        streamer.start(mode=target_mode)

    # Start FastAPI Server unless --no-api was passed
    if not args.no_api:
        if uvicorn:
            app = create_api_app(streamer)
            host = config_manager.get("api", {}).get("host", "0.0.0.0")
            print(f"[Web Dashboard] Running at: http://{host}:{port}")
            print(f"[API Docs] Swagger documentation at: http://{host}:{port}/docs")
            uvicorn.run(app, host=host, port=port, log_level="warning")
        else:
            print("[Warning] uvicorn is not installed. Running in background CLI mode.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                streamer.stop()
    else:
        # CLI only mode
        print("[CLI Mode] Stream running. Press Ctrl+C to terminate.")
        try:
            while streamer.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            streamer.stop()


if __name__ == "__main__":
    main()

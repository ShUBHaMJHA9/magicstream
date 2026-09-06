#!/usr/bin/env python3
"""
================================================================================
MagicStream CLI: Professional 24/7 Multi-Platform Live Broadcast Engine
Author: Shubham Kumar Jha
License: MIT
Repository: https://github.com/shubhamkumarjha/magicstream
================================================================================
Command-line interface and orchestrator for MagicStream.
"""

import os
import sys
import argparse
import threading
import time
from typing import Optional, Tuple
from magicstream import __version__, __author__, __license__
from magicstream.config import ConfigManager
from magicstream.streamer import LiveStreamManager
from magicstream.hardware import HardwareDetector, QUALITY_PROFILES
from magicstream.ffmpeg_builder import FFmpegBuilder
from magicstream.api import create_api_app
from magicstream.ui import (
    get_banner,
    render_hardware_card,
    CYAN,
    YELLOW,
    GREEN,
    RED,
    RESET,
    BOLD,
    DIM,
    WHITE,
    MAGENTA,
)

try:
    import uvicorn
except ImportError:
    uvicorn = None


BANNER = get_banner()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for automated or headless execution."""
    parser = argparse.ArgumentParser(
        prog="magicstream",
        description="MagicStream: Professional 24/7 Live Streaming Engine for YouTube, Facebook, Twitch, Kick & Custom RTMP.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"MagicStream v{__version__} by {__author__}",
        help="Show MagicStream version and exit"
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
        "--log-file", "-l",
        default=None,
        help="Path to stream log file for runtime diagnostics (default: logs/stream.log)"
    )

    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable continuous logging to file"
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


def run_interactive_menu(config_manager: ConfigManager, streamer: LiveStreamManager) -> Tuple[Optional[str], bool]:
    """Sensible, context-aware interactive terminal menu wizard."""
    hw = HardwareDetector.get_system_summary()
    encoder_name = getattr(streamer, "encoder", None) or FFmpegBuilder(config_manager.config).detect_encoder("auto")
    log_file = streamer.log_file_path if streamer.log_to_file else "Disabled"

    print(get_banner())
    print(render_hardware_card(hw, encoder=encoder_name, log_path=log_file) + "\n")

    print(f"{BOLD}{MAGENTA}--- Select MagicStream Execution Mode ---{RESET}")
    print(f"  {CYAN}[T]{RESET} Launch Cyberpunk Terminal Studio & Live Controller {RED}❤️{RESET}")
    print(f"  {CYAN}[1]{RESET} Mode 1: Radio Looper (Looping background video + Audio playlist/stream)")
    print(f"  {CYAN}[2]{RESET} Mode 2: YouTube Relay (Restream YouTube live stream or video directly)")
    print(f"  {CYAN}[3]{RESET} Mode 3: Custom Media (Custom video URL/file + Custom audio URL/file)")
    print(f"  {CYAN}[4]{RESET} Mode 4: Local Playlist 24/7 (Continuous folder-based loop of local clips)")
    print(f"  {CYAN}[5]{RESET} Mode 5: Direct Stream Relay (HLS/m3u8/RTMP restreamer to target)")
    print(f"  {CYAN}[6]{RESET} Web Dashboard & API Server Only")
    print(f"  {CYAN}[7]{RESET} Hardware & Resource Capability Report")
    print(f"  {CYAN}[0]{RESET} Exit")
    print(f"{DIM}{'-' * 76}{RESET}")

    try:
        choice = input("Enter choice [T, 1-7, 0]: ").strip().upper()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        sys.exit(0)

    if choice == "T":
        from magicstream.runner import main as studio_main
        studio_main()
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
        try:
            input("Press Enter to return...")
        except (KeyboardInterrupt, EOFError):
            pass
        return run_interactive_menu(config_manager, streamer)
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice, defaulting to Mode 1 (Radio Looper).")
        return "mode_1_radio", False


def main():
    """Main CLI execution flow for MagicStream."""
    args = parse_arguments()
    config_manager = ConfigManager()

    # Apply CLI Destination Overrides
    if args.platform:
        config_manager.config["destination"]["platform"] = args.platform
    if args.stream_key:
        config_manager.config["destination"]["stream_key"] = args.stream_key
    if args.custom_rtmp:
        config_manager.config["destination"]["custom_rtmp_url"] = args.custom_rtmp

    # Apply Mode Overrides
    selected_mode = normalize_mode(args.mode)
    if selected_mode:
        config_manager.config["streaming"]["mode"] = selected_mode

    # Apply Source Overrides
    if args.video:
        config_manager.config["streaming"]["mode_1_radio"]["video_path"] = args.video
        config_manager.config["streaming"]["mode_3_custom"]["video_source"] = args.video
    if args.audio:
        config_manager.config["streaming"]["mode_1_radio"]["audio_source"] = args.audio
        config_manager.config["streaming"]["mode_3_custom"]["audio_source"] = args.audio
    if args.yt_source:
        config_manager.config["streaming"]["mode_2_yt_relay"]["youtube_source_url"] = args.yt_source

    # Apply Quality and Overlay Overrides
    if args.quality:
        config_manager.config["encoding"]["quality_profile"] = args.quality

    if args.logo:
        config_manager.config["overlay"]["logo_path"] = args.logo
    if args.logo_pos:
        config_manager.config["overlay"]["position"] = args.logo_pos
    if args.no_overlay:
        config_manager.config["overlay"]["enable"] = False

    # Apply Playback Order & Video Selection
    if args.playback_order:
        config_manager.config["streaming"]["playback_order"] = args.playback_order
    if args.video_selection:
        config_manager.config["streaming"]["video_selection"] = args.video_selection

    # Apply Logging Overrides
    if args.log_file:
        config_manager.config["logging"]["file"] = args.log_file
        config_manager.config["logging"]["enabled"] = True
    if args.no_log:
        config_manager.config["logging"]["enabled"] = False

    # Launch Terminal Studio directly if -t / --terminal was passed
    if args.terminal:
        from magicstream.runner import main as studio_main
        studio_main()
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

    print(get_banner())
    hw = HardwareDetector.get_system_summary()
    encoder_name = getattr(streamer, "encoder", None) or FFmpegBuilder(config_manager.config).detect_encoder("auto")
    log_status = streamer.log_file_path if streamer.log_to_file else "Disabled"
    print(render_hardware_card(hw, encoder=encoder_name, log_path=log_status) + "\n")

    print(f"{BOLD}{GREEN}⚡ Starting MagicStream Broadcast Engine...{RESET}")
    print(f"  {CYAN}Mode:{RESET}        {WHITE}{target_mode}{RESET}")
    print(f"  {CYAN}Platform:{RESET}    {WHITE}{platform.upper()}{RESET}")
    print(f"  {CYAN}Profile:{RESET}     {YELLOW}{streamer.active_profile_name}{RESET} {DIM}(Hardware-Adaptive){RESET}")
    print(f"  {CYAN}Diagnostics:{RESET} {GREEN}{log_status}{RESET}\n")

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

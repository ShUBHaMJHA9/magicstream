#!/usr/bin/env python3
"""
================================================================================
MagicStream: Beautiful Terminal Controller & Interactive Broadcast Studio
Crafted with ❤️ by Shubham Kumar Jha
License: MIT
================================================================================
Context-aware guided wizard, pixel-perfect ANSI TUI studio dashboard,
hotkeys, audio shuffle vs sequential loop, and live telemetry.
"""

import os
import re
import sys
import time
import select
import termios
import tty
import unicodedata
from magicstream.config import ConfigManager
from magicstream.streamer import LiveStreamManager
from magicstream.hardware import HardwareDetector, QUALITY_PROFILES
from magicstream.ffmpeg_builder import FFmpegBuilder
from magicstream.ui import (
    get_banner,
    render_hardware_card,
    render_box_top,
    render_box_line,
    render_box_separator,
    render_box_bottom,
    term_width,
    RESET as CLR_RESET,
    BOLD as CLR_BOLD,
    DIM as CLR_DIM,
    ITALIC as CLR_ITALIC,
    RED as CLR_RED,
    GREEN as CLR_GREEN,
    YELLOW as CLR_YELLOW,
    BLUE as CLR_BLUE,
    MAGENTA as CLR_MAGENTA,
    CYAN as CLR_CYAN,
    WHITE as CLR_WHITE,
    BOX_CONTENT,
)


SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
ANSI_REGEX = re.compile(r"\033\[[0-9;]*m")


def clear_screen():
    """Clear terminal screen and place cursor at top."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def prompt_choice(prompt: str, default: str) -> str:
    """Prompt user with clean styling and a default fallback."""
    sys.stdout.write(f"{CLR_WHITE}{prompt} [{CLR_GREEN}{default}{CLR_WHITE}]: {CLR_CYAN}")
    sys.stdout.flush()
    try:
        val = sys.stdin.readline().strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{CLR_RED}Operation cancelled.{CLR_RESET}")
        sys.exit(0)
    sys.stdout.write(CLR_RESET)
    return val if val else default


def interactive_wizard(config_manager: ConfigManager) -> None:
    """Context-aware, sensible guided setup wizard."""
    clear_screen()
    print(get_banner())
    hw = HardwareDetector.get_system_summary()
    encoder_name = FFmpegBuilder(config_manager.config).detect_encoder("auto")
    log_file = config_manager.config.get("logging", {}).get("file", "logs/stream.log")

    print(render_hardware_card(hw, encoder=encoder_name, log_path=log_file) + "\n")


    # Step 1: Destination Platform
    print(f"{CLR_BOLD}{CLR_MAGENTA}--- Step 1: Select Destination Platform ---{CLR_RESET}")
    print(f"  {CLR_CYAN}[1]{CLR_RESET} YouTube Live")
    print(f"  {CLR_CYAN}[2]{CLR_RESET} Facebook Live (RTMPS)")
    print(f"  {CLR_CYAN}[3]{CLR_RESET} Twitch")
    print(f"  {CLR_CYAN}[4]{CLR_RESET} Kick")
    print(f"  {CLR_CYAN}[5]{CLR_RESET} Custom RTMP Server URL")
    plat_choice = prompt_choice("Choose Platform (1-5)", "1")
    plat_map = {"1": "youtube", "2": "facebook", "3": "twitch", "4": "kick", "5": "custom"}
    selected_platform = plat_map.get(plat_choice, "youtube")
    config_manager.config["destination"]["platform"] = selected_platform

    current_key = config_manager.config["destination"].get("stream_key", "")
    if selected_platform == "custom":
        custom_url = prompt_choice("Enter Custom RTMP URL", config_manager.config["destination"].get("custom_rtmp_url", "rtmp://my-server.com/live/key"))
        config_manager.config["destination"]["custom_rtmp_url"] = custom_url
    else:
        disp_key = current_key[:6] + "..." if len(current_key) > 6 else (current_key or "Required")
        new_key = prompt_choice(f"Enter {selected_platform.capitalize()} Stream Key", disp_key)
        if new_key and not new_key.endswith("..."):
            config_manager.config["destination"]["stream_key"] = new_key

    # Step 2: Streaming Mode
    print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Step 2: Select Streaming Mode ---{CLR_RESET}")
    print(f"  {CLR_CYAN}[1]{CLR_RESET} Mode 1: Radio Looper (Looping Video + YouTube Audio Stream / Playlist)")
    print(f"  {CLR_CYAN}[2]{CLR_RESET} Mode 2: YouTube Relay (Restream Live broadcast or video directly)")
    print(f"  {CLR_CYAN}[3]{CLR_RESET} Mode 3: Custom Media Combiner (Custom Video Link/File + Custom Audio)")
    print(f"  {CLR_CYAN}[4]{CLR_RESET} Mode 4: Local Media Playlist 24/7 Looper")
    print(f"  {CLR_CYAN}[5]{CLR_RESET} Mode 5: Direct Stream Relay (HLS/m3u8/RTMP)")
    print(f"  {CLR_CYAN}[6]{CLR_RESET} Mode 6: 24/7 Live Breaking News Channel Studio (AI Speech Anchor + Live Ticker)")
    mode_choice = prompt_choice("Choose Mode (1-6)", "1")
    mode_map = {
        "1": "mode_1_radio",
        "2": "mode_2_yt_relay",
        "3": "mode_3_custom",
        "4": "mode_4_local_playlist",
        "5": "mode_5_direct_relay",
        "6": "mode_6_news",
    }
    selected_mode = mode_map.get(mode_choice, "mode_1_radio")
    config_manager.config["streaming"]["mode"] = selected_mode

    # Step 3: Context-Aware Media Configuration
    if selected_mode == "mode_1_radio":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Radio Looper Media Setup ---{CLR_RESET}")
        default_audio = config_manager.config["streaming"]["mode_1_radio"].get("audio_source", "audio/audio.txt")
        audio_src = prompt_choice("Audio Source (Playlist e.g. audio/audio.txt, or single YouTube URL)", default_audio)
        config_manager.config["streaming"]["mode_1_radio"]["audio_source"] = audio_src

        track_count = 1
        is_multi_track = False
        if os.path.isfile(audio_src):
            try:
                with open(audio_src, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    track_count = len(lines)
                    is_multi_track = track_count > 1
            except Exception:
                pass
        elif os.path.isdir(audio_src):
            files = [f for f in os.listdir(audio_src) if f.endswith((".mp3", ".wav", ".aac", ".flac", ".m4a"))]
            track_count = len(files)
            is_multi_track = track_count > 1

        if is_multi_track:
            print(f"  {CLR_CYAN}Playlist has {track_count} tracks:{CLR_RESET}")
            print(f"  {CLR_CYAN}[1]{CLR_RESET} Sequential One-by-One Loop (Track 1 → 2 → 3...)")
            print(f"  {CLR_CYAN}[2]{CLR_RESET} Random Song Choice / Shuffle Mode 🔀")
            order_choice = prompt_choice("Choose Audio Playback Order (1-2)", "2")
            config_manager.config["streaming"]["playback_order"] = "random" if order_choice == "2" else "sequential"
        else:
            config_manager.config["streaming"]["playback_order"] = "sequential"

        default_video = config_manager.config["streaming"]["mode_1_radio"].get("video_path", "video/vid.mp4")
        video_src = prompt_choice("Background Video (file or video/ folder)", default_video)
        config_manager.config["streaming"]["mode_1_radio"]["video_path"] = video_src

        video_clips_count = 0
        if os.path.isdir(video_src):
            video_clips_count = len([f for f in os.listdir(video_src) if f.endswith((".mp4", ".mkv", ".mov", ".webm"))])
        elif os.path.isdir("video"):
            video_clips_count = len([f for f in os.listdir("video") if f.endswith((".mp4", ".mkv", ".mov", ".webm"))])

        if video_clips_count > 1:
            print(f"  {CLR_CYAN}Found {video_clips_count} video clips in folder:{CLR_RESET}")
            print(f"  {CLR_CYAN}[1]{CLR_RESET} Random Video from folder for each track 🎬")
            print(f"  {CLR_CYAN}[2]{CLR_RESET} Sequential Video Rotation")
            print(f"  {CLR_CYAN}[3]{CLR_RESET} Single Looping Video")
            vid_choice = prompt_choice("Choose Video Style (1-3)", "1")
            if vid_choice == "1":
                config_manager.config["streaming"]["video_selection"] = "random"
            elif vid_choice == "2":
                config_manager.config["streaming"]["video_selection"] = "sequential"
            else:
                config_manager.config["streaming"]["video_selection"] = "single"
        else:
            config_manager.config["streaming"]["video_selection"] = "single"

    elif selected_mode == "mode_2_yt_relay":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- YouTube Live/Video Relay Setup ---{CLR_RESET}")
        default_yt = config_manager.config["streaming"]["mode_2_yt_relay"].get("youtube_source_url", "https://www.youtube.com/watch?v=jfKfPfyJRdk")
        yt_source = prompt_choice("Enter YouTube Video or Live Stream URL", default_yt)
        config_manager.config["streaming"]["mode_2_yt_relay"]["youtube_source_url"] = yt_source
        config_manager.config["streaming"]["playback_order"] = "sequential"
        config_manager.config["streaming"]["video_selection"] = "single"

    elif selected_mode == "mode_3_custom":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Custom Media Combiner Setup ---{CLR_RESET}")
        default_vid = config_manager.config["streaming"]["mode_3_custom"].get("video_source", "video/vid.mp4")
        video_src = prompt_choice("Enter Video Source (File or Direct Video URL)", default_vid)
        config_manager.config["streaming"]["mode_3_custom"]["video_source"] = video_src

        default_aud = config_manager.config["streaming"]["mode_3_custom"].get("audio_source", "audio/audio.txt")
        audio_src = prompt_choice("Enter Audio Source (File, URL, or Playlist)", default_aud)
        config_manager.config["streaming"]["mode_3_custom"]["audio_source"] = audio_src
        config_manager.config["streaming"]["playback_order"] = "sequential"
        config_manager.config["streaming"]["video_selection"] = "single"

    elif selected_mode == "mode_4_local_playlist":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Local Media Playlist Setup ---{CLR_RESET}")
        v_count = len([f for f in os.listdir("video") if f.endswith((".mp4", ".mkv", ".mov", ".webm"))]) if os.path.isdir("video") else 0
        a_count = len([f for f in os.listdir("audio") if f.endswith((".mp3", ".wav", ".aac", ".flac", ".m4a"))]) if os.path.isdir("audio") else 0
        print(f"  Detected {v_count} video files in video/ and {a_count} audio files in audio/")

        if a_count > 1:
            print(f"  {CLR_CYAN}[1]{CLR_RESET} Sequential Loop | {CLR_CYAN}[2]{CLR_RESET} Random Shuffle 🔀")
            order_choice = prompt_choice("Choose Playback Order (1-2)", "2")
            config_manager.config["streaming"]["playback_order"] = "random" if order_choice == "2" else "sequential"
        else:
            config_manager.config["streaming"]["playback_order"] = "sequential"

        if v_count > 1:
            print(f"  {CLR_CYAN}[1]{CLR_RESET} Random Video | {CLR_CYAN}[2]{CLR_RESET} Sequential Rotation | {CLR_CYAN}[3]{CLR_RESET} Single")
            v_choice = prompt_choice("Choose Video Style (1-3)", "1")
            config_manager.config["streaming"]["video_selection"] = "random" if v_choice == "1" else ("sequential" if v_choice == "2" else "single")
        else:
            config_manager.config["streaming"]["video_selection"] = "single"

    elif selected_mode == "mode_5_direct_relay":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Direct Stream Relay Setup ---{CLR_RESET}")
        default_stream = config_manager.config["streaming"]["mode_5_direct_relay"].get("input_stream_url", "https://example.com/live/stream.m3u8")
        stream_url = prompt_choice("Enter HLS (.m3u8) / RTMP / RTSP Stream URL", default_stream)
        config_manager.config["streaming"]["mode_5_direct_relay"]["input_stream_url"] = stream_url
        config_manager.config["streaming"]["playback_order"] = "sequential"
        config_manager.config["streaming"]["video_selection"] = "single"

    elif selected_mode == "mode_6_news":
        print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- 24/7 Live Breaking News Channel Setup ---{CLR_RESET}")
        print(f"  {CLR_CYAN}[1]{CLR_RESET} World News (Google News RSS)")
        print(f"  {CLR_CYAN}[2]{CLR_RESET} India News (National Headlines)")
        print(f"  {CLR_CYAN}[3]{CLR_RESET} Technology & AI News")
        print(f"  {CLR_CYAN}[4]{CLR_RESET} Business & Markets")
        print(f"  {CLR_CYAN}[5]{CLR_RESET} BBC World News RSS")
        cat_choice = prompt_choice("Choose News Category (1-5)", "1")
        cat_map = {"1": "world", "2": "india", "3": "technology", "4": "business", "5": "bbc"}
        config_manager.config["streaming"]["mode_6_news"]["category"] = cat_map.get(cat_choice, "world")

        tts_choice = prompt_choice("Enable AI Speech Anchor (Text-to-Speech)? (Y/N)", "Y").upper()
        config_manager.config["streaming"]["mode_6_news"]["tts_enabled"] = (tts_choice != "N")

        default_video = config_manager.config["streaming"]["mode_6_news"].get("video_path", "video/vid.mp4")
        video_src = prompt_choice("Background Loop Video", default_video)
        config_manager.config["streaming"]["mode_6_news"]["video_path"] = video_src
        config_manager.config["streaming"]["playback_order"] = "sequential"
        config_manager.config["streaming"]["video_selection"] = "single"


    # Step 4: Quality Profile
    print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Step 3: Video Quality Profile ---{CLR_RESET}")
    print(f"  {CLR_CYAN}[A]{CLR_RESET} Auto-Detect ({hw['profile_name']}) - Recommended")
    print(f"  {CLR_CYAN}[U]{CLR_RESET} Ultra-Low (240p @ 15fps, 250k bitrate, 1 thread - 500MB RAM safe)")
    print(f"  {CLR_CYAN}[L]{CLR_RESET} Low (480p @ 24fps, 800k bitrate - 1GB VPS safe)")
    print(f"  {CLR_CYAN}[M]{CLR_RESET} Medium HD (720p @ 30fps, 2500k bitrate)")
    print(f"  {CLR_CYAN}[H]{CLR_RESET} Full HD (1080p @ 30fps, 4500k bitrate)")
    q_choice = prompt_choice("Choose Quality (A/U/L/M/H)", "A").upper()
    q_map = {"A": "auto", "U": "ultra_low", "L": "low", "M": "medium", "H": "high"}
    config_manager.config["encoding"]["quality_profile"] = q_map.get(q_choice, "auto")

    # Step 5: Watermark Logo Overlay
    print(f"\n{CLR_BOLD}{CLR_MAGENTA}--- Step 4: Watermark Logo Overlay ---{CLR_RESET}")
    logo_choice = prompt_choice("Enable Logo Watermark Overlay? (Y/N)", "Y").upper()
    config_manager.config["overlay"]["enable"] = (logo_choice != "N")

    print(f"\n{CLR_GREEN}{CLR_BOLD}✓ Configuration applied successfully! Launching live broadcast studio...{CLR_RESET}")
    time.sleep(1.0)


class NonBlockingInput:
    """Reads single keypresses on Linux without requiring Enter."""

    def __init__(self):
        self.old_settings = None

    def __enter__(self):
        if sys.stdin.isatty():
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                self.old_settings = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass

    def get_key(self) -> Optional[str]:
        if not sys.stdin.isatty():
            return None
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


def run_terminal_studio(streamer: LiveStreamManager) -> None:
    """
    Vibrant terminal live monitor & control studio.
    Provides live animated telemetry, single-key hotkeys, and color logs with clean borders.
    """
    spinner_idx = 0
    running = True

    streamer.silent_console = True
    streamer.start()

    clear_screen()

    with NonBlockingInput() as kb:
        while running:
            status = streamer.get_status()
            is_live = status["is_running"]

            spinner = SPINNER_FRAMES[spinner_idx % len(SPINNER_FRAMES)]
            spinner_idx += 1

            if is_live:
                status_str = f"{CLR_GREEN}{CLR_BOLD}● LIVE BROADCASTING {spinner}{CLR_RESET}"
                status_tag = f"{CLR_GREEN}● LIVE{CLR_RESET}"
            else:
                status_str = f"{CLR_RED}{CLR_BOLD}○ STREAM OFFLINE{CLR_RESET}"
                status_tag = f"{CLR_RED}○ OFFLINE{CLR_RESET}"

            hw = HardwareDetector.get_system_summary()
            profile_name = status.get("profile_info", {}).get("name", status.get("active_profile", "Auto"))

            out = []
            out.append("\033[H")
            out.append(render_box_top("MAGICSTREAM 24/7 BROADCAST STUDIO", status_tag, CLR_CYAN))

            out.append(render_box_line(f"Status:        {status_str}"))
            out.append(render_box_line(f"Platform:      {CLR_CYAN}{status['platform'].upper()}{CLR_RESET}   Mode: {CLR_MAGENTA}{status['mode']}{CLR_RESET}"))
            out.append(render_box_line(f"Quality:       {CLR_YELLOW}{profile_name}{CLR_RESET}   Uptime: {CLR_GREEN}{status['uptime_formatted']}{CLR_RESET}"))
            out.append(render_box_line(f"Hardware:      {CLR_WHITE}{hw['ram_mb']} MB RAM | {hw['cpu_cores']} vCPU Cores | Container Safe{CLR_RESET}"))
            log_file_str = status.get("log_file") or "Disabled"
            out.append(render_box_line(f"Log File:      {CLR_CYAN}{log_file_str}{CLR_RESET} {CLR_DIM}(Continuous Error Tracking){CLR_RESET}"))
            if status.get("last_error"):
                err_preview = status["last_error"]
                if len(err_preview) > 55:
                    err_preview = err_preview[:52] + "..."
                out.append(render_box_line(f"Last Alert:    {CLR_RED}{CLR_BOLD}{err_preview}{CLR_RESET}"))

            out.append(render_box_separator("NOW PLAYING & MEDIA PLAYBACK", CLR_CYAN))

            media_title = status["current_media"]
            if len(media_title) > 55:
                media_title = media_title[:52] + "..."
            out.append(render_box_line(f"Track:         {CLR_WHITE}{CLR_BOLD}{media_title}{CLR_RESET}"))

            track_info = f"Track {status['current_track_index']} of {status['total_tracks']}" if status['total_tracks'] > 0 else "Continuous Stream"
            order_label = "🔀 Random Shuffle" if status['playback_order'] == "random" else "🔁 Sequential Loop"
            out.append(render_box_line(f"Progress:      {CLR_CYAN}{track_info}{CLR_RESET}   Order: {CLR_YELLOW}{order_label}{CLR_RESET}"))

            if status["mode"] in ("mode_1_radio", "mode_4_local_playlist"):
                video_label = status["current_video"]
                if len(video_label) > 55:
                    video_label = video_label[:52] + "..."
                out.append(render_box_line(f"Video BG:      {CLR_BLUE}{video_label}{CLR_RESET}"))

            out.append(render_box_separator("LIVE TELEMETRY LOGS (Realtime)", CLR_CYAN))

            recent = list(streamer.recent_logs)[-5:]
            while len(recent) < 5:
                recent.append("")

            for log_line in recent:
                if not log_line:
                    out.append(render_box_line(""))
                    continue

                if "error" in log_line.lower() or "alert" in log_line.lower():
                    colored_line = f"{CLR_RED}{log_line}{CLR_RESET}"
                elif "speed=" in log_line:
                    colored_line = f"{CLR_CYAN}{log_line}{CLR_RESET}"
                elif "resolving" in log_line.lower() or "started" in log_line.lower() or "success" in log_line.lower():
                    colored_line = f"{CLR_GREEN}{log_line}{CLR_RESET}"
                else:
                    colored_line = f"{CLR_DIM}{log_line}{CLR_RESET}"

                plain = ANSI_REGEX.sub("", log_line)
                if len(plain) > 68:
                    trimmed = plain[:65] + "..."
                    out.append(render_box_line(f"{CLR_DIM}{trimmed}{CLR_RESET}"))
                else:
                    out.append(render_box_line(colored_line))

            out.append(render_box_separator("HOTKEYS & STUDIO CONTROLS", CLR_CYAN))
            if status["mode"] == "mode_6_news":
                out.append(render_box_line(f"{CLR_RED}{CLR_BOLD}[B]{CLR_RESET} Stinger Alert  {CLR_CYAN}[C]{CLR_RESET} News Category  {CLR_GREEN}[N]{CLR_RESET} Next Story  {CLR_YELLOW}[D]{CLR_RESET} Downgrade  {CLR_MAGENTA}[S]{CLR_RESET} Pause  {CLR_RED}[Q]{CLR_RESET} Quit"))
            else:
                out.append(render_box_line(f"{CLR_GREEN}[N]{CLR_RESET} Next Song  {CLR_YELLOW}[P]{CLR_RESET} Toggle Shuffle  {CLR_CYAN}[D]{CLR_RESET} Downgrade  {CLR_MAGENTA}[S]{CLR_RESET} Pause  {CLR_RED}[Q]{CLR_RESET} Quit"))
            out.append(render_box_bottom(CLR_CYAN))

            sys.stdout.write("\n".join(out) + "\n")
            sys.stdout.flush()

            key = kb.get_key()
            if key:
                key = key.lower()
                if key == "q":
                    print(f"\n{CLR_RED}Terminating live broadcast studio...{CLR_RESET}")
                    streamer.stop()
                    running = False
                    break
                elif key == "b":
                    streamer.log("[Hotkey] ⚡ Triggering 3D Breaking News Alert Stinger Intro...")
                    if hasattr(streamer, "trigger_breaking_news_alert"):
                        streamer.trigger_breaking_news_alert()
                elif key == "c":
                    cats = ["world", "india", "technology", "business", "bbc"]
                    curr_cat = streamer.config_manager.config.get("streaming", {}).get("mode_6_news", {}).get("category", "world")
                    next_cat = cats[(cats.index(curr_cat) + 1) % len(cats)] if curr_cat in cats else "world"
                    streamer.config_manager.config["streaming"]["mode_6_news"]["category"] = next_cat
                    streamer.log(f"[Hotkey] News Category switched to: {next_cat.upper()}")
                    if hasattr(streamer, "set_news_category"):
                        streamer.set_news_category(next_cat)
                elif key == "n":
                    streamer.log("[Hotkey] Skipping to next track/headline...")
                    streamer.skip_track()
                elif key == "p":
                    new_order = "sequential" if streamer.playback_order == "random" else "random"
                    streamer.playback_order = new_order
                    streamer.config_manager.config["streaming"]["playback_order"] = new_order
                    streamer.log(f"[Hotkey] Playback order toggled to: {new_order}")
                elif key == "d":
                    lower = HardwareDetector.get_downgraded_profile_name(streamer.active_profile_name)
                    streamer.log(f"[Hotkey] Force downgraded profile to: {lower}")
                    streamer.active_profile_name = lower
                    if streamer.active_process:
                        streamer.active_process.terminate()
                elif key == "s":
                    if streamer.is_running:
                        streamer.log("[Hotkey] Pausing live stream...")
                        streamer.stop()
                    else:
                        streamer.log("[Hotkey] Resuming live stream...")
                        streamer.start()

            time.sleep(0.35)


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(get_banner())
        print("Usage: magicstream-studio [OPTIONS]")
        print("\nOptions:")
        print("  -h, --help    Show this help message and exit")
        print("\nHotkeys inside Studio:")
        print("  [N] Skip to next track immediately")
        print("  [P] Toggle playback order (Random Shuffle vs Sequential Loop)")
        print("  [D] Force downgrade quality profile by 1 tier (if machine is lagging)")
        print("  [S] Pause / Resume live stream")
        print("  [Q] Quit studio and terminate stream safely")
        print(f"\nCrafted with ❤️ by Shubham Kumar Jha | License: MIT\n")
        return

    clear_screen()
    config_manager = ConfigManager()
    interactive_wizard(config_manager)


    streamer = LiveStreamManager(config_manager)
    streamer.playback_order = config_manager.config["streaming"].get("playback_order", "sequential")
    streamer.video_selection = config_manager.config["streaming"].get("video_selection", "single")

    try:
        run_terminal_studio(streamer)
    except KeyboardInterrupt:
        print(f"\n{CLR_YELLOW}Received shutdown signal. Stopping live stream cleanly...{CLR_RESET}")
        streamer.stop()
    finally:
        print(f"{CLR_GREEN}MagicStream broadcast studio stopped cleanly. Crafted with ❤️ by Shubham Kumar Jha!{CLR_RESET}")


if __name__ == "__main__":
    main()

<div align="center">

# ⚡ MagicStream: 24/7 Multi-Platform Live Broadcast Studio

**Enterprise-grade, adaptive 24/7 live streaming engine and Python library for YouTube Live, Facebook Live, Twitch, Kick & Custom RTMP servers.**

[![PyPI Version](https://img.shields.io/badge/pip-magicstream-blue.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-5.0%2B-green.svg?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Shubham%20Kumar%20Jha-red.svg?style=for-the-badge)](https://github.com/shubhamkumarjha)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-quickstart-guide">Quickstart</a> •
  <a href="#-cyberpunk-terminal-studio">Terminal Studio</a> •
  <a href="#-streaming-modes">Streaming Modes</a> •
  <a href="#-continuous-error-logging">Error Logging</a> •
  <a href="#-adaptive-hardware-engine">Adaptive Hardware</a> •
  <a href="#-python-sdk-usage">Python SDK</a> •
  <a href="#-web-dashboard--rest-api">Web Dashboard</a> •
  <a href="#-docker-deployment">Docker</a> •
  <a href="#-license">License</a>
</p>

---

```
  __  __             _      ____  _                              
 |  \/  | __ _  __ _(_) ___/ ___|| |_ _ __ ___  __ _ _ __ ___   
 | |\/| |/ _` |/ _` | |/ __\___ \| __| '__/ _ \/ _` | '_ ` _ \  
 | |  | | (_| | (_| | | (__ ___) | |_| | |  __/ (_| | | | | | | 
 |_|  |_|\__,_|\__, |_|\___|____/ \__|_|  \___|\__,_|_| |_| |_| 
               |___/                                            
  ⚡ 24/7 MULTI-PLATFORM LIVE BROADCAST STUDIO ⚡
  >> Crafted with ❤️ by Shubham Kumar Jha | MIT License | v2.0.0 Stable <<

╭─── [ SYSTEM HARDWARE & ADAPTIVE PROFILE ] ──────────────────── [ ● READY ] ╮
│  RAM Capacity:    [███████████░] 7322 MB (7.15 GB) • Container Safe        │
│  CPU Allocation:  [█████████░░░] 12.0 vCPU Cores • Real-Time Engine        │
│  Active Encoder:  ⚡ libopenh264 (H.264 Zero-Lag Auto-Detected)            │
│  Recommended:     💎 Full HD (1080p) (Adaptive Auto-Tuned)                 │
│  Adaptive Guard:  🛡️  Auto-Downgrade Active (Watchdog: < 0.85x)            │
│  Diagnostic Logs: 📄 logs/stream.log (Continuous Realtime)                 │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

</div>

## 🌟 Key Features

- **🚀 5 Powerful Streaming Modes**:
  1. **Radio Looper**: Infinite video background loop with online YouTube audio stream or playlist. Supports **Random Song Shuffle** 🔀 or **Sequential Loop** 🔁.
  2. **YouTube Video/Live Relay**: Directly restream any YouTube live broadcast or video with custom logo overlay and zero disk download footprint.
  3. **Custom Media Combiner**: Mix any remote or local video source with any custom audio source on the fly.
  4. **Local Playlist 24/7 Looper**: Continuous, seamless looping through a folder of videos and audio tracks.
  5. **Direct Stream Relay**: Restream HLS (`.m3u8`), RTMP, or RTSP camera feeds directly.
- **🌐 Multi-Platform Broadcast**:
  - Stream concurrently or independently to **YouTube Live**, **Facebook Live (RTMPS)**, **Twitch**, **Kick**, or any **Custom RTMP/RTMPS** destination.
- **⚡ Direct YouTube Streaming without Disk Downloads**:
  - Automatically resolves YouTube URLs on the fly using `yt-dlp` into high-quality direct HTTP/HLS streaming feeds (`googlevideo.com` / `.m3u8`). Zero hard disk wear, zero temporary download files.
- **🛡️ Adaptive Hardware Engine (Runs from 500MB RAM & 0.1 vCPU to 16+ Cores)**:
  - Automatically detects host and Docker cgroups memory and CPU limits.
  - Active encoding watchdog (`speed < 0.85x`) automatically triggers profile auto-downgrades (1080p → 720p → 480p → 240p) to guarantee non-stop 24/7 uptime without crashes.
- **📄 Continuous Diagnostic Error Logging (`logs/stream.log`)**:
  - Persistent, thread-safe, auto-rotating log file captures every streamer event, YouTube extraction warning, and raw FFmpeg stderr output for effortless troubleshooting.
- **🎛️ Cyberpunk Terminal Studio & Live Controller**:
  - Interactive ASCII TUI dashboard with live telemetry, elapsed time, current song metadata, and instant hotkeys (`[N]` Next Song, `[P]` Toggle Shuffle, `[D]` Force Downgrade, `[S]` Pause/Resume, `[Q]` Clean Exit).
- **📦 Dual Distribution: Pip Package & CLI Tool**:
  - Install as a global CLI tool or import as a Python SDK (`from magicstream import LiveStreamManager`).

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python**: Version 3.9+ (`python3 --version`)
- **FFmpeg**: Installed on system (`ffmpeg -version`)

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg librsvg2-bin

# Fedora / RHEL
sudo dnf install -y ffmpeg librsvg2-tools

# Arch Linux / Manjaro
sudo pacman -S ffmpeg librsvg

# macOS (Homebrew)
brew install ffmpeg librsvg
```

### 2. Installation

You can install MagicStream directly from source as a pip package:

```bash
git clone https://github.com/shubhamkumarjha/YT_LIVE.git
cd YT_LIVE

# Install as editable pip package
pip install -e .
```

This registers two global console commands:
- **`magicstream`**: The full CLI engine, daemon runner, and API server.
- **`magicstream-studio`**: The interactive cyberpunk terminal broadcast studio.

---

## 🎛️ Cyberpunk Terminal Studio

To launch the animated, colorful Terminal Studio with hotkey controls:

```bash
magicstream-studio
# or
magicstream -t
```

### Studio Hotkeys:
| Hotkey | Action |
| :---: | :--- |
| **`[N]`** | Skip to next song / track immediately |
| **`[P]`** | Toggle playback order between **Random Shuffle** 🔀 and **Sequential Loop** 🔁 |
| **`[D]`** | Force downgrade active quality profile by 1 tier (e.g. 1080p → 720p) |
| **`[S]`** | Pause / Resume live broadcast cleanly |
| **`[Q]`** | Clean shutdown (gracefully terminates FFmpeg and child threads) |

---

## 🎮 CLI Usage & Streaming Modes

```bash
# Interactive Setup Wizard
magicstream -i

# Mode 1: Radio Looper (Looping background video + YouTube audio playlist)
magicstream --mode 1 --platform youtube --stream-key "xxxx-xxxx-xxxx-xxxx"

# Mode 1 with Random Song Shuffle
magicstream --mode 1 --playback-order random --video-selection random

# Mode 2: YouTube Video / Live Restream Relay
magicstream --mode 2 --yt-source "https://www.youtube.com/watch?v=jfKfPfyJRdk"

# Mode 3: Custom Media Combiner
magicstream --mode 3 --video "https://example.com/video.mp4" --audio "https://example.com/stream.mp3"

# Mode 4: Local Playlist 24/7 Looper
magicstream --mode 4

# Mode 5: Direct Stream Relay (HLS/m3u8/RTMP)
magicstream --mode 5 --video "https://example.com/live/playlist.m3u8"
```

---

## 📄 Continuous Error Logging

MagicStream writes all runtime logs and raw FFmpeg error diagnostics continuously into:
```
logs/stream.log
```
- **Auto-Rotation**: Log files automatically rotate at 10MB to prevent filling up disk space.
- **Error Dumps**: Whenever a streaming process exits unexpectedly, MagicStream extracts and logs the last 15 lines of FFmpeg stderr to instantly highlight root causes (e.g. invalid stream key, network drop, codec mismatch).
- **Web Download**: Access raw logs from the web dashboard at `GET /logs/file` or inspect live events at `GET /logs`.

To specify a custom log file or disable file logging:
```bash
magicstream --log-file /var/log/my_stream.log
# or disable:
magicstream --no-log
```

---

## 🛡️ Adaptive Hardware Engine

MagicStream is designed to run seamlessly on machines from **500MB RAM & 0.1 vCPU VPS** up to dedicated high-end broadcast servers.

| Profile | Target Hardware | Resolution | FPS | Bitrate | Audio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ultra_low`** | 500MB–1GB RAM, 0.1–0.5 vCPU | 426x240 | 15 fps | 250 kbps | 64 kbps |
| **`low`** | 1GB–2GB RAM, 1 vCPU | 854x480 | 24 fps | 800 kbps | 96 kbps |
| **`medium`** | 2GB–4GB RAM, 2 vCPUs | 1280x720 | 30 fps | 2500 kbps | 128 kbps |
| **`high`** | 4GB+ RAM, 4+ vCPUs or GPU | 1920x1080 | 30 fps | 4500 kbps | 160 kbps |

*Note: Output encoding strictly follows hardware profile detection, ensuring low-spec devices never overload.*

---

## 🐍 Python SDK Usage

You can use MagicStream directly inside your Python applications:

```python
from magicstream import LiveStreamManager, ConfigManager, HardwareDetector

# Inspect system hardware capabilities
hw = HardwareDetector.get_system_summary()
print(f"Detected RAM: {hw['ram_mb']} MB | Cores: {hw['cpu_cores']} | Profile: {hw['profile_name']}")

# Load and customize configuration
config = ConfigManager()
config.config["destination"]["platform"] = "youtube"
config.config["destination"]["stream_key"] = "xxxx-xxxx-xxxx-xxxx"
config.config["streaming"]["mode"] = "mode_1_radio"

# Start the broadcast manager
streamer = LiveStreamManager(config)
streamer.start()

# Query live status
status = streamer.get_status()
print(f"Broadcasting: {status['is_running']} | Profile: {status['active_profile']}")

# Clean shutdown
streamer.stop()
```

---

## 🖥️ Web Dashboard & REST API

MagicStream includes a built-in FastAPI web controller:

```bash
# Start API server alongside live stream (default port 8000)
magicstream --port 8000

# Start API server only
magicstream --api-only --port 8000
```

Dashboard URL: **`http://localhost:8000`**  
Interactive Swagger Docs: **`http://localhost:8000/docs`**

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Responsive Web Dashboard with live status and controls |
| `GET` | `/status` | Real-time JSON telemetry (uptime, active mode, hardware, PID) |
| `GET` | `/hardware` | System RAM, CPU cores, and profile report |
| `POST` | `/start` | Start live streaming with optional overrides |
| `POST` | `/stop` | Stop live streaming immediately |
| `POST` | `/skip` | Skip to next track in playlist |
| `POST` | `/set-quality` | Dynamically change active quality profile |
| `GET` | `/logs` | Fetch the last 100 log lines |
| `GET` | `/logs/file` | Download full persistent `stream.log` diagnostic file |

---

## 🐳 Docker Deployment

Deploy with Docker Compose:

```bash
docker compose up -d
```

View real-time logs:
```bash
docker compose logs -f
```

---

## 📄 License & Credits

Crafted with ❤️ by **[Shubham Kumar Jha](https://github.com/shubhamkumarjha)**.  
Released under the **[MIT License](LICENSE)**.

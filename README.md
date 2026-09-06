<div align="center">

# ⚡ MagicStream: 24/7 Multi-Platform Live Broadcast Studio

**Enterprise-grade, adaptive 24/7 live streaming engine and Python library for YouTube Live, Facebook Live, Twitch, Kick & Custom RTMP servers.**

[![GitHub Repo](https://img.shields.io/badge/GitHub-ShUBHaMJHA9%2Fmagicstream-181717.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ShUBHaMJHA9/magicstream)
[![PyPI Version](https://img.shields.io/badge/pip-magicstream-blue.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-5.0%2B-green.svg?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Shubham%20Kumar%20Jha-red.svg?style=for-the-badge)](https://github.com/ShUBHaMJHA9)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-quickstart-guide">Quickstart</a> •
  <a href="#-cyberpunk-terminal-studio">Terminal Studio</a> •
  <a href="#-streaming-modes">Streaming Modes</a> •
  <a href="#-on-screen-display--tv-graphics">On-Screen Graphics</a> •
  <a href="#-architecture--module-reference">Architecture & Modules</a> •
  <a href="#-continuous-error-logging">Error Logging</a> •
  <a href="#-adaptive-hardware-engine">Adaptive Hardware</a> •
  <a href="#-python-sdk-usage">Python SDK</a> •
  <a href="#-web-dashboard--rest-api">Web Dashboard</a> •
  <a href="#-docker-deployment">Docker</a> •
  <a href="#-how-to-contribute">Contributing</a> •
  <a href="#-acknowledgments--open-source-credits">Thanks & Credits</a> •
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
│  Active Encoder:  ⚡ libopenh264 / libx264 (H.264 Zero-Lag Auto-Detected)   │
│  Recommended:     💎 Full HD (1080p) (Adaptive Auto-Tuned)                 │
│  Adaptive Guard:  🛡️  Auto-Downgrade Active (Watchdog: < 0.85x)            │
│  Diagnostic Logs: 📄 logs/stream.log (Continuous Realtime)                 │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

</div>

## 🌟 Key Features

- **🚀 6 Powerful Broadcast Modes**:
  1. **Radio Looper (with TV Music Channel Card)**: Infinite background video loop with online YouTube audio streams or local playlists. Displays live Zee Music / MTV-style glassmorphic **"NOW PLAYING"** & **"UP NEXT"** on-screen lower-thirds. Supports **Random Song Shuffle** 🔀 or **Sequential Loop** 🔁.
  2. **YouTube Video / Live Restream Relay**: Restream any YouTube live broadcast or video with custom logo overlay and zero local disk download footprint.
  3. **Custom Media Combiner**: Mix any remote or local video source with any custom audio source on the fly.
  4. **Local Playlist 24/7 Looper**: Seamless looping through entire directories of videos and audio tracks.
  5. **Direct Stream Relay**: Direct restreaming of HLS (`.m3u8`), RTMP, or RTSP feeds.
  6. **24/7 Live Breaking News Channel Studio**: Automated live TV news channel with live RSS news scraping (Google News, BBC, Reuters), an AI speech anchor (TTS), breaking news lower-third banners, and a live rolling news ticker.
- **📺 Broadcast-Grade On-Screen Display (OSD)**:
  - **Zee Music / MTV Music Card**: Glassmorphism lower-third displaying animated sound wave equalizers, track titles, and upcoming songs.
  - **CNN / BBC Breaking News Lower-Third**: Bold red broadcast banner with live headlines, source attribution badges, and rolling ticker.
  - **Scalable Watermark Logo**: Multi-position vector (SVG) or raster (PNG) brand overlay with adjustable alpha transparency.
- **⚡ Direct YouTube Streaming without Disk Downloads**:
  - Resolves YouTube URLs in real time via `yt-dlp` into high-quality direct HTTP/HLS streaming feeds (`googlevideo.com` / `.m3u8`). Zero hard disk wear, zero temporary download files.
- **🛡️ Adaptive Hardware Engine (Runs on 500MB RAM VPS up to 32-Core Servers)**:
  - Automatically measures host and Docker cgroups memory and CPU limits.
  - Real-time encoding watchdog (`speed < 0.85x`) automatically triggers profile auto-downgrades (1080p → 720p → 480p → 240p) to prevent frame drops or stream disconnection.
- **📄 Continuous Diagnostic Error Logging (`logs/stream.log`)**:
  - Persistent, thread-safe, auto-rotating log file captures every streamer event, YouTube extraction warning, and raw FFmpeg stderr output for effortless debugging.
- **🎛️ Cyberpunk Terminal Studio & Live Hotkey Controller**:
  - Interactive ASCII TUI dashboard with live telemetry, elapsed time, current song metadata, and instant hotkeys (`[N]` Next Song, `[P]` Toggle Shuffle, `[D]` Force Downgrade, `[S]` Pause/Resume, `[Q]` Clean Exit).
- **🌐 Multi-Platform Broadcast**:
  - Broadcast concurrently or independently to **YouTube Live**, **Facebook Live (RTMPS)**, **Twitch**, **Kick**, or any **Custom RTMP/RTMPS** destination.
- **📦 Dual Distribution: Pip Package & Standalone CLI**:
  - Install as a global console utility or import as a Python SDK (`from magicstream import LiveStreamManager`).

---

## ⚡ Quickstart Guide

### 1. System Prerequisites
- **Python**: Version 3.9 or higher (`python3 --version`)
- **FFmpeg**: Installed with H.264 support (`ffmpeg -version`)
- **librsvg**: For real-time SVG vector rendering onto video streams

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg librsvg2-bin python3-pip

# Fedora / RHEL
sudo dnf install -y ffmpeg librsvg2-tools python3-pip

# Arch Linux / Manjaro
sudo pacman -S ffmpeg librsvg python-pip

# macOS (Homebrew)
brew install ffmpeg librsvg python
```

### 2. Installation

Clone from GitHub and install as a pip package:

```bash
git clone https://github.com/ShUBHaMJHA9/magicstream.git
cd magicstream

# Install in editable development mode
pip install -e .
```

This registers two global console commands:
- **`magicstream`**: The core streaming daemon, CLI launcher, and API server.
- **`magicstream-studio`**: The interactive cyberpunk terminal broadcast studio.

---

## 🎛️ Cyberpunk Terminal Studio

To launch the animated, colorful Terminal Studio with interactive hotkeys:

```bash
magicstream-studio
# or
magicstream -t
```

### Live Studio Hotkeys:
| Hotkey | Action | Description |
| :---: | :--- | :--- |
| **`[N]`** | Next Song / Track | Instantly skips to the next track in the playlist |
| **`[P]`** | Toggle Playback Mode | Switches between **Random Shuffle** 🔀 and **Sequential Loop** 🔁 |
| **`[D]`** | Dynamic Downgrade | Drops current stream resolution by one tier (e.g. 1080p → 720p) |
| **`[S]`** | Pause / Resume | Safely pauses the live broadcast without crashing |
| **`[Q]`** | Clean Shutdown | Gracefully terminates FFmpeg and exits all worker threads |

---

## 📺 Streaming Modes

### Mode 1: 24/7 Lo-Fi Radio Looper + Music Channel Card
Loops a background video (or cycles through a directory of video clips) while streaming YouTube tracks or local audio files. Features an on-screen glassmorphic card showing **NOW PLAYING** and **UP NEXT**:

```bash
# Interactive setup wizard
magicstream -i

# Run Mode 1 directly with custom stream key
magicstream --mode 1 --platform youtube --stream-key "xxxx-xxxx-xxxx-xxxx"

# Enable Random Song Shuffle with Random Video Clips
magicstream --mode 1 --playback-order random --video-selection random
```

### Mode 2: YouTube Video / Live Restream Relay
Directly relays any existing YouTube live stream or video without downloading it to disk:

```bash
magicstream --mode 2 --yt-source "https://www.youtube.com/watch?v=jfKfPfyJRdk"
```

### Mode 3: Custom Media Combiner
Combines any video source (local file or direct URL) with any audio source:

```bash
magicstream --mode 3 --video "video/background.mp4" --audio "https://example.com/stream.mp3"
```

### Mode 4: Local Media Playlist Looper
Loops through a folder of local video clips and audio files:

```bash
magicstream --mode 4
```

### Mode 5: Direct Stream Relay
Restreams live HLS (`.m3u8`), RTMP, or RTSP feeds:

```bash
magicstream --mode 5 --video "https://example.com/live/playlist.m3u8"
```

### Mode 6: 24/7 Live Breaking News Channel Studio
An automated, round-the-clock television news channel. Scrapes live breaking headlines from free, open RSS feeds (Google News, BBC, Reuters, Tech), generates an AI speech bulletin (TTS), renders a dynamic CNN/BBC-style red lower-third card, and streams continuously:

```bash
# Launch News Channel (Google News World headlines + AI voice anchor)
magicstream --mode 6

# News mode with specific category
magicstream --mode 6 --category technology
```

---

## 🎨 On-Screen Display & TV Graphics

MagicStream features real-time vector compositing via FFmpeg's `librsvg` filter, eliminating the need for expensive GPU rendering pipelines.

### 1. MTV / Zee Music "Now Playing" Lower-Third Card
- Displays in bottom-left corner of the broadcast.
- Includes animated audio equalizer bars, current song title, upcoming track name, and glowing channel badge.
- Automatically generated and updated as each new song starts.

### 2. CNN / BBC Breaking News Lower-Third Banner
- Full-width broadcast lower-third in high-impact broadcast red.
- Displays `🔴 BREAKING NEWS`, news source badge, clean headline typography, and a scrolling headline ticker.

### 3. Corner Watermark Logo
- Vector SVG or high-resolution PNG overlay.
- Configurable position (`top-right`, `top-left`, `bottom-right`, `bottom-left`), margins, scaling, and opacity.

---

## 🏗️ Architecture & Module Reference

MagicStream is engineered as a modular, production-ready live streaming framework:

```
magicstream/
├── __init__.py           # Package exports & version metadata
├── cli.py                # Command-line entrypoints & argument parser
├── runner.py             # Cyberpunk Terminal Studio TUI & interactive wizard
├── streamer.py           # LiveStreamManager: central orchestration & stream loops
├── ffmpeg_builder.py     # Hardware-adaptive FFmpeg command & filtergraph builder
├── extractor.py          # StreamUrlExtractor: zero-disk yt-dlp direct stream resolver
├── overlay_generator.py  # OverlayGenerator: vector SVG music cards & news graphics
├── news_engine.py        # NewsFetcher & NewsBroadcastStudio: RSS & TTS news pipeline
├── hardware.py           # HardwareDetector: cgroups & hardware auto-tuning
├── config.py             # ConfigManager: YAML, env, and CLI configuration cascade
├── logger.py             # StreamLogger: thread-safe auto-rotating diagnostic logger
├── api.py                # FastAPI REST controller & embedded HTML5 dashboard
└── ui.py                 # ANSI color palettes, ASCII banners, and UI components
```

### Module Breakdown:

| Module | Core Classes | Responsibility |
| :--- | :--- | :--- |
| **`magicstream.streamer`** | `LiveStreamManager` | Manages active stream processes, thread-safe start/stop/pause/skip cycles, multi-mode loops, and auto-reconnect logic. |
| **`magicstream.ffmpeg_builder`** | `FFmpegBuilder` | Constructs hardware-optimized FFmpeg commands, encoder detection (libx264, h264_nvenc, h264_vaapi), and multi-input overlay filtergraphs. |
| **`magicstream.extractor`** | `StreamUrlExtractor` | Uses `yt-dlp` to extract direct streaming video/audio URLs on the fly with smart metadata caching. |
| **`magicstream.overlay_generator`** | `OverlayGenerator` | Generates SVG broadcast overlays: Zee Music cards, Breaking News lower-thirds, and equalizer badges. |
| **`magicstream.news_engine`** | `NewsFetcher`, `NewsBroadcastStudio` | Zero-API RSS headline scraper and Google Text-to-Speech (`gTTS`) audio bulletin generator. |
| **`magicstream.hardware`** | `HardwareDetector` | Detects container memory limits, vCPU core allocations, and calculates adaptive quality profiles. |
| **`magicstream.runner`** | `MagicStreamRunner`, `NonBlockingInput` | Cyberpunk terminal dashboard, live telemetry refresh loop, and non-blocking Linux terminal key listener. |
| **`magicstream.config`** | `ConfigManager` | Deep-merging configuration loader supporting CLI args, environment variables, YAML files, and fallbacks. |
| **`magicstream.logger`** | `StreamLogger` | Continuous diagnostic logging into `logs/stream.log` with auto-rotation (10MB) and FFmpeg crash dumps. |
| **`magicstream.api`** | `create_api_app` | High-performance FastAPI application serving REST endpoints and an embedded responsive web dashboard. |

---

## 📄 Continuous Error Logging

MagicStream logs all runtime events, stream state changes, and raw FFmpeg errors continuously into:
```
logs/stream.log
```
- **Auto-Rotation**: Log files automatically rotate at 10MB to prevent disk exhaustion.
- **Raw FFmpeg Error Dumps**: If FFmpeg exits unexpectedly, the last 15 lines of stderr are captured and written to `logs/stream.log` to immediately identify the root cause (e.g., bad stream key, network drop, incompatible audio codec).
- **Web Download**: Access raw logs from the web dashboard at `GET /logs/file` or inspect recent events via `GET /logs`.

---

## 🛡️ Adaptive Hardware Engine

MagicStream is specifically designed to run reliably on resource-constrained cloud servers:

| Profile | Target Hardware | Resolution | FPS | Bitrate | Audio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ultra_low`** | 500MB–1GB RAM, 0.1–0.5 vCPU | 426x240 | 15 fps | 250 kbps | 64 kbps |
| **`low`** | 1GB–2GB RAM, 1 vCPU | 854x480 | 24 fps | 800 kbps | 96 kbps |
| **`medium`** | 2GB–4GB RAM, 2 vCPUs | 1280x720 | 30 fps | 2500 kbps | 128 kbps |
| **`high`** | 4GB+ RAM, 4+ vCPUs or GPU | 1920x1080 | 30 fps | 4500 kbps | 160 kbps |

*Note: The dynamic watchdog monitors encoding speed. If speed drops below 0.85x in real time, MagicStream automatically drops down one profile tier to keep the broadcast live without stutter.*

---

## 🐍 Python SDK Usage

Import and control MagicStream inside your own Python projects:

```python
from magicstream import LiveStreamManager, ConfigManager, HardwareDetector

# Inspect system hardware capabilities
hw = HardwareDetector.get_system_summary()
print(f"RAM: {hw['ram_mb']} MB | vCPUs: {hw['cpu_cores']} | Profile: {hw['profile_name']}")

# Load and customize configuration
config = ConfigManager("config.yaml")
config.config["destination"]["platform"] = "youtube"
config.config["destination"]["stream_key"] = "xxxx-xxxx-xxxx-xxxx"
config.config["streaming"]["mode"] = "mode_1_radio"

# Start the broadcast manager
streamer = LiveStreamManager(config)
streamer.start()

# Query live status
status = streamer.get_status()
print(f"Live: {status['is_running']} | Profile: {status['active_profile']}")

# Graceful shutdown
# streamer.stop()
```

---

## 🖥️ Web Dashboard & REST API

Control your live stream from any browser or HTTP client:

```bash
# Start API server alongside live stream (port 8000)
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
| `POST` | `/start` | Start live streaming with optional config overrides |
| `POST` | `/stop` | Stop live streaming cleanly |
| `POST` | `/skip` | Skip to the next track in the playlist |
| `POST` | `/set-quality` | Dynamically switch quality profiles |
| `GET` | `/logs` | Fetch the last 100 log lines in JSON format |
| `GET` | `/logs/file` | Download full persistent `stream.log` diagnostic file |

---

## 🐳 Docker Deployment

Run MagicStream inside a containerized environment using Docker Compose:

```bash
# Build and run in detached mode
docker compose up -d

# View live broadcast logs
docker compose logs -f
```

---

## 🤝 How to Contribute

We welcome contributions from developers, creators, and streamers worldwide! Whether it is adding new broadcast modes, optimizing FFmpeg filtergraphs, improving the web UI, or fixing bugs:

1. **Fork the Repository**:
   Click the **Fork** button at the top right of [https://github.com/ShUBHaMJHA9/magicstream](https://github.com/ShUBHaMJHA9/magicstream).

2. **Clone your Fork**:
   ```bash
   git clone https://github.com/<your-username>/magicstream.git
   cd magicstream
   ```

3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

4. **Install in Development Mode**:
   ```bash
   pip install -e .
   ```

5. **Commit your Changes**:
   ```bash
   git commit -m "feat: add amazing new feature"
   ```

6. **Push to your Branch & Open a Pull Request**:
   ```bash
   git push origin feature/amazing-new-feature
   ```
   Open a PR against the `main` branch with a clear description of your changes.

---

## 💖 Acknowledgments & Open-Source Credits

MagicStream stands on the shoulders of giants. We express our deepest gratitude and appreciation to the authors, maintainers, and communities of the following incredible open-source projects:

- **[FFmpeg](https://ffmpeg.org/)** — The undisputed gold standard of multimedia processing. Without FFmpeg's unparalleled transcoding, filtering, and RTMP streaming capabilities, this project would not be possible.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — The extraordinary, robust media extraction library that allows MagicStream to resolve online YouTube streams in real time with zero disk footprint.
- **[FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/)** — For powering our ultra-fast, modern asynchronous REST API and Web Dashboard controller with automatic OpenAPI documentation.
- **[gTTS (Google Text-to-Speech)](https://github.com/pndurette/gTTS)** — For enabling our automated 24/7 AI Breaking News Channel to synthesize realistic spoken news bulletins without requiring paid third-party voice APIs.
- **[librsvg](https://wiki.gnome.org/Projects/LibRsvg)** — For providing lightning-fast SVG vector rendering directly within FFmpeg's video filtergraph, enabling beautiful dynamic glassmorphic music cards and breaking news lower-thirds.
- **[Pydantic](https://docs.pydantic.dev/)** — For robust, elegant data validation and schema management.
- **[PyYAML](https://pyyaml.org/)** — For reliable, clean configuration file parsing.
- **[psutil](https://github.com/giampaolo/psutil)** — For cross-platform hardware, memory, and CPU utilization monitoring.
- **The Global Open-Source Community** — For continuous inspiration, knowledge sharing, and dedication to free software.

---

## 📄 License

Crafted with ❤️ by **[Shubham Kumar Jha](https://github.com/ShUBHaMJHA9)**.  
Released under the **[MIT License](LICENSE)**. Feel free to use, modify, and distribute for personal or commercial broadcast projects!

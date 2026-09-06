# Video Directory (`video/`)

This directory is dedicated to storing local video loops, background clips, and video playlist files for the **YT_LIVE** streaming engine.

## Structure & Usage

### 1. Looping Background Video
- For **Mode 1 (Radio Looper)**, drop your looping background video here.
- Default filename: `vid.mp4` (configurable in `config.yaml` or via `--video` CLI argument).
- The video will automatically loop infinitely while the audio track or live radio plays over it.

### 2. Supported Formats
- `.mp4` (H.264 / AVC - Highly Recommended)
- `.mkv` (Matroska)
- `.webm` (VP8 / VP9)
- `.mov` (QuickTime)
- `.ts` / `.m2ts` (MPEG Transport Stream)

### 3. Recommendations for 24/7 Live Streaming
| Preset | Resolution | Target FPS | Video Bitrate | Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Full HD** | 1920x1080 | 30 / 60 fps | 4500 - 6000 kbps | High (H.264) |
| **HD Standard** | 1280x720 | 30 fps | 2500 - 3500 kbps | Main (H.264) |
| **Radio / Low-Resource** | 854x480 or 426x240 | 15 / 30 fps | 300 - 800 kbps | Baseline / Main |

> [!TIP]
> Keep your looping video encoded as H.264 (`yuv420p` pixel format) with a closed GOP (`keyint=30` or `keyint=60`) for seamless looping and minimal CPU usage.

# Audio Directory (`audio/`)

This directory is dedicated to storing local audio files and audio playlist files for the **MagicStream** broadcast engine.


## Structure & Usage

### 1. Remote Audio URL Playlist (`audio.txt`)
Store YouTube video/stream URLs, live radio streams, or direct `.mp3`/`.aac`/`.m3u8` stream links, one per line:
```text
https://www.youtube.com/watch?v=F-FGwn4D_EY
https://www.youtube.com/watch?v=jfKfPfyJRdk
https://ice1.somafm.com/groovesalad-128-mp3
```
- The streamer will play these audio tracks in sequence or loop continuously.
- Empty lines and lines starting with `#` (comments) are automatically ignored.

### 2. Local Audio Files
You can drop any local audio files directly into this directory:
- **Supported Formats**: `.mp3`, `.wav`, `.aac`, `.flac`, `.m4a`, `.ogg`, `.opus`
- **Recommended Codec**: AAC or MP3 (44.1 kHz or 48 kHz stereo, 128kbps–320kbps)

When running **Mode 4 (Local Playlist Looper)**, the streaming engine can automatically detect and loop all local audio files in this directory.

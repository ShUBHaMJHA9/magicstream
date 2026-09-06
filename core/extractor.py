"""
Media URL Extractor Module using yt-dlp
Author: Shubham Kumar Jha
License: MIT

Extracts direct audio and video stream URLs from YouTube and other platforms,
handling live streams, playlists, authentication cookies, and token expiration.
"""

import os
import time
from typing import Dict, Any, Optional, List

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class MediaExtractor:
    """Extracts streaming URLs for live streams, videos, and playlists."""

    def __init__(self, cookie_file: Optional[str] = "cookies.txt"):
        self.cookie_file = cookie_file if cookie_file and os.path.exists(cookie_file) else None
        self._url_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 3600 * 2  # 2 hours default cache TTL

    def _get_ydl_options(self, audio_only: bool = False, quality: str = "best") -> Dict[str, Any]:
        """Build yt-dlp extraction options with mobile client bypasses for bot blocks."""
        if audio_only:
            format_spec = "bestaudio/best/18"
        else:
            if quality == "1080p":
                format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best/18"
            elif quality == "720p":
                format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]/best/18"
            elif quality == "480p":
                format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]/best/18"
            else:
                format_spec = "bestvideo+bestaudio/best/18"

        opts: Dict[str, Any] = {
            "format": format_spec,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "mweb", "web"],
                    "skip": ["authcheck"],
                }
            },
        }

        if self.cookie_file and os.path.exists(self.cookie_file):
            opts["cookiefile"] = self.cookie_file

        return opts

    def extract_audio_url(self, url: str, force_refresh: bool = False) -> Optional[str]:
        """Extract best direct audio stream URL from a given link."""
        if not url:
            return None

        # If it's already a direct audio/stream file or local file, return directly
        if url.startswith(("http://", "https://")) and url.endswith((".mp3", ".aac", ".m4a", ".wav", ".m3u8")):
            return url
        if os.path.exists(url):
            return url

        # Check cache
        cache_key = f"audio_{url}"
        now = time.time()
        if not force_refresh and cache_key in self._url_cache:
            entry = self._url_cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl_seconds:
                return entry["stream_url"]

        if yt_dlp is None:
            print("[MediaExtractor] Error: yt-dlp is not installed.")
            return None

        opts = self._get_ydl_options(audio_only=True)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                stream_url = info.get("url")
                if stream_url:
                    self._url_cache[cache_key] = {"stream_url": stream_url, "timestamp": now}
                return stream_url
        except Exception as e:
            print(f"[MediaExtractor] Failed to extract audio from '{url}': {e}")
            return None

    def extract_video_stream(self, url: str, quality: str = "best", force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract direct video and audio streaming URLs for restreaming.
        Returns a dict with 'video_url', 'audio_url', 'title', 'is_live'.
        """
        if not url:
            return None

        # Check if local file or direct m3u8
        if os.path.exists(url) or url.endswith(".m3u8"):
            return {"video_url": url, "audio_url": url, "title": os.path.basename(url), "is_live": False}

        cache_key = f"video_{quality}_{url}"
        now = time.time()
        if not force_refresh and cache_key in self._url_cache:
            entry = self._url_cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl_seconds:
                return entry["data"]

        if yt_dlp is None:
            print("[MediaExtractor] Error: yt-dlp is not installed.")
            return None

        opts = self._get_ydl_options(audio_only=False, quality=quality)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                video_url = info.get("url")
                audio_url = None

                # Fallback: search available formats for best stream with valid URL
                if not video_url:
                    formats = info.get("formats", [])
                    valid = [f for f in formats if f.get("url") and f.get("vcodec") != "none"]
                    if valid:
                        best_f = valid[-1]
                        video_url = best_f.get("url")
                        audio_url = best_f.get("url")

                result = {
                    "video_url": video_url,
                    "audio_url": audio_url,
                    "title": info.get("title", "Live Stream"),
                    "is_live": info.get("is_live", False),
                    "duration": info.get("duration", 0),
                }

                if video_url:
                    self._url_cache[cache_key] = {"data": result, "timestamp": now}
                return result
        except Exception as e:
            print(f"[MediaExtractor] Failed to extract video stream from '{url}': {e}")
            return None

    def parse_playlist_file(self, file_path: str) -> List[str]:
        """Reads a list of URLs or file paths from a text playlist file."""
        if not os.path.exists(file_path):
            print(f"[MediaExtractor] Playlist file not found: {file_path}")
            return []

        urls = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("#"):
                        urls.append(cleaned)
        except Exception as e:
            print(f"[MediaExtractor] Error reading playlist '{file_path}': {e}")

        return urls

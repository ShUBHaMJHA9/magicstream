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
    """Extracts streaming URLs for live streams, videos, and playlists with bulletproof cookie support."""

    def __init__(self, cookie_file: Optional[str] = "cookies.txt", cookies_from_browser: Optional[str] = None):
        self.cookie_file = self._resolve_cookie_file(cookie_file)
        self.cookies_from_browser = cookies_from_browser
        self._url_cache: Dict[str, Dict[str, Any]] = {}
        self._title_cache: Dict[str, str] = {}
        self.cache_ttl_seconds = 3600 * 2
        self.last_error: Optional[str] = None

    @classmethod
    def _resolve_cookie_file(cls, cookie_file: Optional[str] = "cookies.txt") -> Optional[str]:
        """
        Robustly locate and validate the YouTube cookies.txt file across
        custom paths, current working directory, project root, and environment variables.
        Essential for VPS / cloud server streaming to bypass YouTube bot detection.
        """
        candidates: List[str] = []
        if cookie_file:
            candidates.append(cookie_file)
            if not os.path.isabs(cookie_file):
                candidates.append(os.path.abspath(cookie_file))
                # Project root relative to magicstream package
                pkg_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(pkg_dir)
                candidates.append(os.path.join(project_root, cookie_file))

        # Check environment variables
        for env_var in ["MAGICSTREAM_COOKIES", "YT_COOKIES", "YOUTUBE_COOKIES_PATH", "COOKIES_FILE"]:
            val = os.environ.get(env_var)
            if val:
                candidates.append(val)
                if not os.path.isabs(val):
                    candidates.append(os.path.abspath(val))

        # Common fallback locations
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(pkg_dir)
        candidates.extend([
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(project_root, "cookies.txt"),
            os.path.expanduser("~/.config/magicstream/cookies.txt"),
            os.path.expanduser("~/cookies.txt"),
        ])

        # Deduplicate candidates preserving order
        seen = set()
        deduped = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                deduped.append(c)

        for path in deduped:
            if os.path.isfile(path):
                size = os.path.getsize(path)
                if size > 0:
                    clean_path = cls._sanitize_cookie_file(os.path.abspath(path))
                    cls._inspect_cookie_file(clean_path)
                    return clean_path

        print("[MagicStream Extractor] ⚠️ WARNING: No valid 'cookies.txt' file found in any expected location.")
        print("[MagicStream Extractor] ⚠️ YouTube blocks VPS / Datacenter IPs with 'Sign in to confirm you’re not a bot'.")
        print("[MagicStream Extractor] ⚠️ Passing cookies is COMPULSORY for VPS streaming!")
        print("[MagicStream Extractor] 💡 Fix: Place your exported cookies.txt in the project root or use --cookies <path>.")
        return None

    @classmethod
    def _sanitize_cookie_file(cls, path: str) -> str:
        """
        Sanitizes cookies.txt file to ensure it is strictly compliant with
        MozillaCookieJar / Netscape specifications.
        Automatically repairs stray editor characters (like 'v# Netscape', BOM markers, leading blank lines).
        """
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            needs_repair = False
            first_line = content.split("\n", 1)[0] if content else ""
            if not first_line.startswith("# Netscape HTTP Cookie File") and not first_line.startswith("# HTTP Cookie File"):
                needs_repair = True
            if content.startswith("\ufeff"):
                needs_repair = True

            if needs_repair:
                lines = content.splitlines()
                cleaned_lines = ["# Netscape HTTP Cookie File", "# This is a generated file! Do not edit.", ""]
                header_skipped = False
                for line in lines:
                    stripped = line.strip()
                    if not header_skipped and ("HTTP Cookie File" in line or "cookie_spec" in line or "generated file" in line):
                        continue
                    header_skipped = True
                    if not stripped:
                        continue
                    cleaned_lines.append(line)

                cleaned_content = "\n".join(cleaned_lines) + "\n"
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(cleaned_content)
                    print(f"[MagicStream Extractor] 🩹 Auto-repaired corrupted Netscape cookie header in '{path}'!")
                except Exception as write_err:
                    print(f"[MagicStream Extractor] Note: Could not write clean cookies.txt in-place: {write_err}")
        except Exception as e:
            print(f"[MagicStream Extractor] Warning during cookie sanitization: {e}")
        return path

    @classmethod
    def _inspect_cookie_file(cls, path: str) -> None:
        """Inspect and log diagnostic details about the cookie file."""
        size = os.path.getsize(path)
        has_youtube = False
        has_auth = False
        auth_tokens = ["__Secure-1PSID", "__Secure-3PSID", "SID", "LOGIN_INFO", "SSID", "HSID"]
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(8192)
                if "youtube.com" in content or ".youtube.com" in content:
                    has_youtube = True
                for token in auth_tokens:
                    if token in content:
                        has_auth = True
                        break
        except Exception:
            pass

        auth_tag = "Authenticated Session (VPS Ready)" if has_auth else "Guest/Visitor Session (Export signed-in cookies for VPS)"
        print(f"[MagicStream Extractor] 🍪 YouTube Cookie File: '{os.path.abspath(path)}' ({size} bytes)")
        print(f"[MagicStream Extractor] 🔒 Cookie Status: {auth_tag}")
        if not has_auth and has_youtube:
            print("[MagicStream Extractor] ℹ️  Tip: If your VPS gets 'Sign in to confirm you’re not a bot', export cookies while logged into YouTube.")

    def get_title(self, url: str) -> str:
        """Returns cached or extracted human-readable title of media."""
        if not url:
            return ""
        if not url.startswith(("http://", "https://")):
            return os.path.splitext(os.path.basename(url))[0]
        return self._title_cache.get(url, os.path.basename(url))

    def _get_ydl_options(self, audio_only: bool = False, quality: str = "best", client_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build yt-dlp extraction options with cookie support, robust format fallbacks, and mobile client bypasses."""
        if audio_only:
            format_spec = "ba/ba*/bestaudio/best/18"
        else:
            if quality == "1080p":
                format_spec = "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b/18/best"
            elif quality == "720p":
                format_spec = "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b/18/best"
            elif quality in ("480p", "low"):
                format_spec = "bv*[height<=480]+ba/b[height<=480]/bv*+ba/b/18/best"
            else:
                format_spec = "bv*+ba/b/18/best"

        opts: Dict[str, Any] = {
            "format": format_spec,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
        }

        # Android client completely avoids 'The page needs to be reloaded' web interstitials
        # while using authenticated session cookies for full resolution
        clients = client_list or ["android", "ios", "mweb", "web"]

        opts["extractor_args"] = {
            "youtube": {
                "player_client": clients,
                "skip": ["authcheck"],
            }
        }

        if self.cookie_file and os.path.isfile(self.cookie_file):
            opts["cookiefile"] = self.cookie_file
        elif self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser,)

        return opts

    def extract_audio_url(self, url: str, force_refresh: bool = False) -> Optional[str]:
        """Extract best direct audio stream URL from a given link with multi-client fallback."""
        if not url:
            return None

        if url.startswith(("http://", "https://")) and url.endswith((".mp3", ".aac", ".m4a", ".wav", ".m3u8")):
            return url
        if os.path.exists(url):
            return url

        cache_key = f"audio_{url}"
        now = time.time()
        if not force_refresh and cache_key in self._url_cache:
            entry = self._url_cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl_seconds:
                return entry["stream_url"]

        if yt_dlp is None:
            print("[MagicStream Extractor] Error: yt-dlp is not installed.")
            return None

        client_tiers = [
            ["android", "ios", "mweb", "web"],
            ["android"],
            ["web", "mweb"],
        ]

        for clients in client_tiers:
            opts = self._get_ydl_options(audio_only=True, client_list=clients)
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        continue

                    if info.get("title"):
                        self._title_cache[url] = info["title"]

                    stream_url = info.get("url")
                    if not stream_url:
                        formats = info.get("formats", [])
                        valid = [f for f in formats if f.get("url") and f.get("acodec") != "none"]
                        if valid:
                            stream_url = valid[-1].get("url")

                    if stream_url:
                        self._url_cache[cache_key] = {"stream_url": stream_url, "timestamp": now}
                        return stream_url
            except Exception as e:
                self.last_error = str(e)
                continue

        err_str = self.last_error or "Unknown extraction failure"
        print(f"[MagicStream Extractor] Failed to extract audio from '{url}': {err_str}")
        self._handle_extraction_error(err_str)
        return None

    def _handle_extraction_error(self, err_str: str) -> None:
        """Provide detailed, actionable diagnostics for common YouTube VPS issues."""
        err_lower = err_str.lower()
        if "bot" in err_lower or "sign in" in err_lower or "confirm you're not a bot" in err_lower:
            print("[MagicStream Extractor] ❌ [YOUTUBE BOT DETECTION ON VPS]")
            if self.cookie_file:
                print(f"[MagicStream Extractor] ⚠️ Your cookies file ('{self.cookie_file}') was passed to yt-dlp, but YouTube rejected it.")
                print("[MagicStream Extractor] 💡 Reasons:")
                print("   1. Cookies were exported while NOT logged in (guest/visitor cookies only).")
                print("   2. Your YouTube session expired or Google invalidated the tokens.")
                print("   👉 Solution: Open Chrome/Firefox -> Sign into YouTube -> Export cookies using 'Get cookies.txt LOCALLY' -> Upload to VPS cookies.txt")
            else:
                print("[MagicStream Extractor] ⚠️ No cookies.txt was found or loaded!")
                print("[MagicStream Extractor] 💡 On VPS / Cloud Datacenter IPs, passing cookies is COMPULSORY.")
                print("   👉 Solution: Export cookies.txt from your browser and place it in the project root.")
        elif "page needs to be reloaded" in err_lower:
            print("[MagicStream Extractor] ℹ️ YouTube web reload interstitial bypassed via android client fallback.")
        elif "requested format is not available" in err_lower or "sabr" in err_lower:
            print("[MagicStream Extractor] ℹ️ Tip: YouTube format selection active. Adjusting player client fallback.")

    def extract_video_stream(self, url: str, quality: str = "best", force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract direct video and audio streaming URLs for restreaming with multi-client fallback.
        Returns a dict with 'video_url', 'audio_url', 'title', 'is_live'.
        """
        if not url:
            return None

        if os.path.exists(url) or url.endswith(".m3u8"):
            return {"video_url": url, "audio_url": url, "title": os.path.basename(url), "is_live": False}

        cache_key = f"video_{quality}_{url}"
        now = time.time()
        if not force_refresh and cache_key in self._url_cache:
            entry = self._url_cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl_seconds:
                return entry["data"]

        if yt_dlp is None:
            print("[MagicStream Extractor] Error: yt-dlp is not installed.")
            return None

        client_tiers = [
            ["android", "ios", "mweb", "web"],
            ["android"],
            ["web", "mweb"],
        ]

        attempts = [(clients, quality) for clients in client_tiers] + [(["android"], "best"), (["android", "web"], "best")]

        for clients, q in attempts:
            opts = self._get_ydl_options(audio_only=False, quality=q, client_list=clients)
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        continue

                    video_url = info.get("url")
                    audio_url = None

                    requested_formats = info.get("requested_formats")
                    if requested_formats and len(requested_formats) >= 2:
                        video_url = requested_formats[0].get("url")
                        audio_url = requested_formats[1].get("url")
                    elif not audio_url:
                        audio_url = video_url

                    # Fallback: search available formats for best stream with valid URL
                    if not video_url:
                        formats = info.get("formats", [])
                        valid = [f for f in formats if f.get("url") and f.get("vcodec") != "none"]
                        if valid:
                            best_f = valid[-1]
                            video_url = best_f.get("url")
                            if best_f.get("acodec") != "none":
                                audio_url = video_url
                            else:
                                audio_valid = [f for f in formats if f.get("url") and f.get("acodec") != "none"]
                                audio_url = audio_valid[-1].get("url") if audio_valid else video_url

                    if video_url:
                        result = {
                            "video_url": video_url,
                            "audio_url": audio_url,
                            "title": info.get("title", "Live Stream"),
                            "is_live": info.get("is_live", False),
                            "duration": info.get("duration", 0),
                        }
                        self._url_cache[cache_key] = {"data": result, "timestamp": now}
                        return result
            except Exception as e:
                self.last_error = str(e)
                continue

        err_str = self.last_error or "Unknown extraction failure"
        print(f"[MagicStream Extractor] Failed to extract video stream from '{url}': {err_str}")
        self._handle_extraction_error(err_str)
        return None


    def parse_playlist_file(self, file_path: str) -> List[str]:
        """Reads a list of URLs or file paths from a text playlist file."""
        if not os.path.exists(file_path):
            print(f"[MagicStream Extractor] Playlist file not found: {file_path}")
            return []

        urls = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("#"):
                        urls.append(cleaned)
        except Exception as e:
            print(f"[MagicStream Extractor] Error reading playlist '{file_path}': {e}")

        return urls

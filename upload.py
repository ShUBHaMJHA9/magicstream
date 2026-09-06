"""
================================================================================
YT_LIVE: Automated Video Scheduler & Chunked Uploader
Author: Shubham Kumar Jha
License: MIT
================================================================================
Monitors configured YouTube channels for newly published videos within a sliding
time window, downloads highest quality media with thumbnails & metadata, and
uploads chunks reliably to an external distribution API.
"""

import os
import sqlite3
import time
import requests
from datetime import datetime, timezone, timedelta
from typing import Set, Dict, Any, Optional, List

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    BackgroundScheduler = None

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


# ------------------------------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ------------------------------------------------------------------------------
MAX_TITLE = 100
MAX_DESC = 5000
MAX_TAGS = 10
CUSTOM_DESCRIPTION = "\n\n🎬 Thanks for WATCHING! 🎧\n🔥 Subscribe to Music Daily 2.0 \n✨ | DAILY MUSIC ✨"

CHANNEL_IDS = [
    'UClFlcWzBQ4rClgbCBuVu_ig',
    'UCHl6jJK8cM8ARh0KE4YGgnw',
    'UCKinQchwHeJHcOs9x4JYVqA'
]
USER_ID = os.getenv("UPLOAD_USER_ID", "eternal")
API_BASE = os.getenv("UPLOAD_API_BASE", "https://youtube-uplod.vercel.app")
DB_FILE = os.getenv("UPLOAD_DB_FILE", "video_db.sqlite")

UPLOAD_INTERVAL = 30     # Minutes between consecutive uploads
CHECK_INTERVAL = 24      # Hours between automated channel scans
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB maximum download size
CHUNK_SIZE = 4 * 1024 * 1024            # 4 MB chunk size for resilient upload
MAX_AGE_HOURS = 24       # Check for videos published within past 24 hours
MAX_UPLOADS_PER_DAY = 20 # Safety cap for daily uploads

# ------------------------------------------------------------------------------
# DATABASE INITIALIZATION
# ------------------------------------------------------------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS uploaded_videos
             (video_id TEXT PRIMARY KEY, 
              channel_id TEXT,
              uploaded_at TEXT,
              status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS upload_lock 
             (lock INTEGER PRIMARY KEY CHECK (lock = 1))''')
conn.commit()


def get_existing_videos() -> Set[str]:
    """Retrieve set of already uploaded video IDs from SQLite."""
    c.execute("SELECT video_id FROM uploaded_videos")
    return {row[0] for row in c.fetchall()}


def get_upload_count_last_24_hours() -> int:
    """Calculates number of videos uploaded in the past 24 hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    c.execute("SELECT uploaded_at FROM uploaded_videos")
    count = 0
    for (uploaded_at_str,) in c.fetchall():
        try:
            uploaded_at = datetime.fromisoformat(uploaded_at_str)
            if uploaded_at >= cutoff:
                count += 1
        except Exception as e:
            print(f"[UploadScheduler] Error parsing date '{uploaded_at_str}': {e}")
    return count


def acquire_lock() -> bool:
    """Atomic SQLite lock to prevent multiple concurrent upload tasks."""
    try:
        c.execute("INSERT INTO upload_lock VALUES (1)")
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def release_lock() -> None:
    """Releases the database upload lock."""
    c.execute("DELETE FROM upload_lock")
    conn.commit()


def cleanup_files(video_id: str) -> None:
    """Removes temporary downloaded artifacts after upload completes."""
    for ext in ['webp', 'jpg', 'jpeg', 'json', 'mp4', 'mkv', 'webm']:
        file_path = f"{video_id}.{ext}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[UploadScheduler] Cleaned up temporary file: {file_path}")
            except Exception as e:
                print(f"[UploadScheduler] Error deleting {file_path}: {e}")


def fetch_channel_videos(channel_id: str) -> List[Dict[str, Any]]:
    """Scrapes latest videos from a YouTube channel within MAX_AGE_HOURS."""
    print(f"[UploadScheduler] Scanning channel {channel_id} for new videos...")
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'mweb'], 'skip': ['authcheck']}},
        'daterange': yt_dlp.utils.DateRange((datetime.now() - timedelta(hours=MAX_AGE_HOURS)).strftime('%Y%m%d'))
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(
                f"https://www.youtube.com/channel/{channel_id}/videos",
                download=False
            )
            existing = get_existing_videos()
            entries = result.get('entries', [])
            return [entry for entry in entries if entry.get('id') not in existing]
    except Exception as e:
        print(f"[UploadScheduler] Error fetching videos for channel {channel_id}: {e}")
        return []


def download_video(video_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Downloads video with best video + best audio streams."""
    try:
        ydl_opts = {
            'outtmpl': '%(id)s.%(ext)s',
            'writethumbnail': True,
            'writeinfojson': True,
            'format': 'bestvideo+bestaudio/best/18',
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'filesize_limit': MAX_FILE_SIZE,
            'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'mweb'], 'skip': ['authcheck']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_info['url'], download=True)
    except Exception as e:
        print(f"[UploadScheduler] Download failed for {video_info.get('id')}: {e}")
        return None


def upload_video(video_path: str, metadata: Dict[str, Any]) -> Optional[str]:
    """Uploads video file in chunks with progress bar to API endpoint."""
    try:
        full_description = f"{metadata.get('description', '')[:MAX_DESC - len(CUSTOM_DESCRIPTION)]}{CUSTOM_DESCRIPTION}"
        
        init_response = requests.post(
            f"{API_BASE}/init",
            data={
                "user_id": USER_ID,
                "file_name": os.path.basename(video_path),
                "file_size": os.path.getsize(video_path),
                "title": metadata.get('title', '')[:MAX_TITLE],
                "description": full_description,
                "tags": ",".join(metadata.get('tags', [])[:MAX_TAGS]),
                "category_id": "22",
                "privacy_status": "public"
            },
            timeout=30
        )
        init_response.raise_for_status()
        upload_id = init_response.json().get('upload_id')

        total_size = os.path.getsize(video_path)
        with open(video_path, 'rb') as f:
            chunk_index = 0
            if tqdm:
                pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc='Uploading')
            else:
                pbar = None

            while chunk := f.read(CHUNK_SIZE):
                requests.post(
                    f"{API_BASE}/chunk/{upload_id}",
                    files={'chunk': (os.path.basename(video_path), chunk)},
                    data={'chunk_index': chunk_index},
                    timeout=30
                ).raise_for_status()
                chunk_index += 1
                if pbar:
                    pbar.update(len(chunk))

            if pbar:
                pbar.close()

        final_response = requests.post(f"{API_BASE}/finalize/{upload_id}", timeout=30)
        final_response.raise_for_status()
        return final_response.json().get('video_id')

    except Exception as e:
        print(f"[UploadScheduler] Upload failed for {video_path}: {e}")
        return None


def process_videos():
    """Main processing loop for channel checking and uploading."""
    if not acquire_lock():
        print("[UploadScheduler] Upload task already in progress. Skipping cycle...")
        return

    try:
        uploads_today = get_upload_count_last_24_hours()
        if uploads_today >= MAX_UPLOADS_PER_DAY:
            print(f"[UploadScheduler] Daily upload limit reached ({uploads_today}/{MAX_UPLOADS_PER_DAY}). Skipping...")
            return

        for channel_id in CHANNEL_IDS:
            videos = fetch_channel_videos(channel_id)
            first_video = True
            for video in videos:
                if get_upload_count_last_24_hours() >= MAX_UPLOADS_PER_DAY:
                    print("[UploadScheduler] Daily upload limit reached mid-batch. Halting.")
                    return

                start_time = time.time()
                info = download_video(video)
                if info:
                    video_path = f"{info['id']}.{info['ext']}"
                    video_id = upload_video(video_path, info)
                    if video_id:
                        c.execute(
                            "INSERT INTO uploaded_videos VALUES (?, ?, ?, ?)",
                            (video['id'], channel_id, datetime.now(timezone.utc).isoformat(), 'uploaded')
                        )
                        conn.commit()
                        print(f"[UploadScheduler] Successfully uploaded video {video['id']}.")
                    cleanup_files(info['id'])

                if not first_video:
                    elapsed = time.time() - start_time
                    sleep_time = max(0, UPLOAD_INTERVAL * 60 - elapsed)
                    if sleep_time > 0:
                        print(f"[UploadScheduler] Cooldown: waiting {sleep_time/60:.1f} minutes...")
                        time.sleep(sleep_time)
                else:
                    first_video = False
    finally:
        release_lock()


def main():
    if not BackgroundScheduler:
        print("[UploadScheduler] Error: APScheduler is required to run automated scheduling.")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_videos,
        'interval',
        hours=CHECK_INTERVAL,
        next_run_time=datetime.now(timezone.utc) + timedelta(minutes=1),
        max_instances=1
    )
    scheduler.start()
    print("[UploadScheduler] Scheduler started. Checking every 24 hours.")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("[UploadScheduler] Shutting down scheduler...")
        scheduler.shutdown()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

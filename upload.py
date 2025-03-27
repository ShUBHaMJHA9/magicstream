import os
import sqlite3
import time
import requests
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from tqdm import tqdm

# Constants
MAX_TITLE = 100
MAX_DESC = 5000
MAX_TAGS = 10
CUSTOM_DESCRIPTION = "\n\n🎬 Thanks for WATCHING! 🎧\n🔥 Subscribe to Music Daily 2.0 \n✨ | DAILY MUSIC ✨"

# Configuration
CHANNEL_IDS = ['UClFlcWzBQ4rClgbCBuVu_ig', 'UCHl6jJK8cM8ARh0KE4YGgnw', "UCKinQchwHeJHcOs9x4JYVqA"]
USER_ID = "eternal"
API_BASE = "https://youtube-uplod.vercel.app"
DB_FILE = "video_db.sqlite"
UPLOAD_INTERVAL = 30  # Minutes between uploads (applied only after the first video)
CHECK_INTERVAL = 24   # Hours between channel checks
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks
MAX_AGE_HOURS = 24  # Check for videos in the last 24 hours

# NEW: Maximum uploads allowed per day (adjust as needed)
MAX_UPLOADS_PER_DAY = 20

# Initialize database
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

def get_existing_videos():
    c.execute("SELECT video_id FROM uploaded_videos")
    return {row[0] for row in c.fetchall()}

def get_upload_count_last_24_hours():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    c.execute("SELECT uploaded_at FROM uploaded_videos")
    count = 0
    for (uploaded_at_str,) in c.fetchall():
        try:
            uploaded_at = datetime.fromisoformat(uploaded_at_str)
            if uploaded_at >= cutoff:
                count += 1
        except Exception as e:
            print(f"Error parsing date: {uploaded_at_str} - {e}")
    return count

def acquire_lock():
    try:
        c.execute("INSERT INTO upload_lock VALUES (1)")
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def release_lock():
    c.execute("DELETE FROM upload_lock")
    conn.commit()

def cleanup_files(video_id):
    for ext in ['webp', 'jpg', 'json', 'mp4', 'mkv', 'webm']:
        file_path = f"{video_id}.{ext}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")

def fetch_channel_videos(channel_id):
    print(f"Checking channel {channel_id} for new videos...")
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        # Removed force_generic_extractor to let the proper YouTube extractor run
        'cookiefile': 'cookies.txt',
        'extractor_args': {'youtubetab': 'skip=authcheck'},
        'daterange': yt_dlp.utils.DateRange((datetime.now() - timedelta(hours=MAX_AGE_HOURS)).strftime('%Y%m%d'))
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(
                f"https://www.youtube.com/channel/{channel_id}/videos",
                download=False
            )
            return [entry for entry in result['entries'] if entry['id'] not in get_existing_videos()]
    except Exception as e:
        print(f"Error fetching videos: {str(e)}")
        return []

def download_video(video_info):
    try:
        ydl_opts = {
            'outtmpl': '%(id)s.%(ext)s',
            'writethumbnail': True,
            'writeinfojson': True,
            'format': 'bestvideo+bestaudio/best',
            'cookiefile': 'cookies.txt',
            'filesize_limit': MAX_FILE_SIZE,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_info['url'], download=True)
    except Exception as e:
        print(f"Download failed: {str(e)}")
        return None

def upload_video(video_path, metadata):
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

        with open(video_path, 'rb') as f, tqdm(
            total=os.path.getsize(video_path), unit='B', unit_scale=True, desc='Uploading'
        ) as pbar:
            chunk_index = 0
            while chunk := f.read(CHUNK_SIZE):
                requests.post(
                    f"{API_BASE}/chunk/{upload_id}",
                    files={'chunk': (os.path.basename(video_path), chunk)},
                    data={'chunk_index': chunk_index},
                    timeout=30
                ).raise_for_status()
                chunk_index += 1
                pbar.update(len(chunk))

        final_response = requests.post(f"{API_BASE}/finalize/{upload_id}", timeout=30)
        final_response.raise_for_status()
        return final_response.json().get('video_id')

    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return None

def process_videos():
    if not acquire_lock():
        print("Upload already in progress. Skipping...")
        return

    try:
        # Check if today's upload limit is reached
        uploads_today = get_upload_count_last_24_hours()
        if uploads_today >= MAX_UPLOADS_PER_DAY:
            print(f"Daily upload limit reached ({uploads_today}/{MAX_UPLOADS_PER_DAY}). Skipping uploads.")
            return

        for channel_id in CHANNEL_IDS:
            videos = fetch_channel_videos(channel_id)
            first_video = True  # Process first video without delay
            for video in videos:
                if get_upload_count_last_24_hours() >= MAX_UPLOADS_PER_DAY:
                    print("Daily upload limit reached during processing. Stopping further uploads.")
                    return

                start_time = time.time()
                if info := download_video(video):
                    video_path = f"{info['id']}.{info['ext']}"
                    if video_id := upload_video(video_path, info):
                        # Update database immediately upon successful upload
                        c.execute("INSERT INTO uploaded_videos VALUES (?, ?, ?, ?)",
                                  (video['id'], channel_id, datetime.now(timezone.utc).isoformat(), 'uploaded'))
                        conn.commit()
                        print(f"Uploaded video {video['id']} successfully and updated database.")
                    cleanup_files(info['id'])
                
                # For subsequent videos, add the upload delay
                if not first_video:
                    elapsed = time.time() - start_time
                    if elapsed < UPLOAD_INTERVAL * 60:
                        sleep_time = UPLOAD_INTERVAL * 60 - elapsed
                        print(f"Waiting {sleep_time/60:.1f} minutes for next upload...")
                        time.sleep(sleep_time)
                else:
                    first_video = False
    finally:
        release_lock()

def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_videos,
        'interval',
        hours=CHECK_INTERVAL,
        next_run_time=datetime.now(timezone.utc) + timedelta(minutes=1),
        max_instances=1
    )
    scheduler.start()
    
    try:
        while True:
            time.sleep(3600)  # Check hourly
    except KeyboardInterrupt:
        scheduler.shutdown()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

import os
import subprocess
import yt_dlp
import threading
import time

# Base directory for handling file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to extract audio URLs from a file
def extract_audio_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            audio_urls = file.readlines()
        return [url.strip() for url in audio_urls if url.strip()]  # Filter out empty lines and strip whitespace
    except Exception as e:
        print(f"Error reading audio URLs from file: {e}")
        return []

# Function to extract audio stream URL from a YouTube link
def extract_audio_from_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': os.path.join(BASE_DIR, 'cookies.txt')  # Include cookies if needed
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(youtube_url, download=False)
            audio_url = info_dict.get('url', None)
            if audio_url:
                return audio_url
            else:
                print(f"No audio stream available for {youtube_url}")
                return None
        except yt_dlp.utils.DownloadError as e:
            print(f"Error extracting audio from {youtube_url}: {e}")
            return None

# Function to stream audio with FFmpeg
def stream_audio(audio_url, looping_video_path, output_url):
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-loglevel', 'info', '-re',
            '-stream_loop', '-1', '-i', looping_video_path,  # Loop the video infinitely
            '-i', audio_url,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '200k', '-maxrate', '200k', '-bufsize', '400k',
            '-r', '15', '-s', '640x360', '-vf', 'format=yuv420p', '-g', '30', '-shortest',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',  # Audio conversion to AAC
            '-map', '0:v', '-map', '1:a',
            '-f', 'flv', output_url
        ]
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error streaming audio: {e}")
    except Exception as e:
        print(f"Unexpected error streaming audio: {e}")

# Streaming logic
def start_streaming(stream_info):
    # Paths to audio file and looping video
    audio_file = os.path.join(BASE_DIR, stream_info['audio_url_file'])
    looping_video = os.path.join(BASE_DIR, stream_info['looping_video_path'])

    # Validate paths
    if not os.path.exists(audio_file) or not os.path.exists(looping_video):
        print("Error: Missing required files.")
        return

    # Extract audio URLs
    audio_urls = extract_audio_from_file(audio_file)
    if not audio_urls:
        print("Error: No audio URLs found in the file.")
        return

    # Output streaming URL
    output_url = 'rtmp://a.rtmp.youtube.com/live2/' + stream_info['stream_key']

    # Loop through audio URLs and stream them
    while True:
        for audio_url in audio_urls:
            extracted_audio_url = extract_audio_from_url(audio_url)
            if extracted_audio_url is not None:
                stream_audio(extracted_audio_url, looping_video, output_url)
            else:
                print(f"Error: Unable to extract audio from {audio_url}")

        # Short delay between loops
        time.sleep(1)

# Entry point
def main():
    # Load streaming information
    streaming_info = [
        {
            'stream_key': os.getenv('STREAM_KEY'),  # Set your stream key as an environment variable
            'looping_video_path': 'vid.mp4',  # Path to looping video
            'audio_url_file': 'audio.txt'  # Path to audio URLs file
        }
    ]

    # Validate environment variables
    for info in streaming_info:
        if not info['stream_key']:
            print("Error: Missing STREAM_KEY environment variable.")
            return

    # Start threads for streaming
    threads = []
    for info in streaming_info:
        thread = threading.Thread(target=start_streaming, args=(info,))
        threads.append(thread)
        thread.start()

    # Wait for threads to finish
    for thread in threads:
        thread.join()

# Run the script
if __name__ == "__main__":
    main()

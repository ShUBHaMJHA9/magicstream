import subprocess
import yt_dlp
import threading
import time

def extract_audio_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            audio_urls = file.readlines()
        return [url.strip() for url in audio_urls if url.strip()]  # Filter out empty lines and strip whitespace
    except Exception as e:
        print(f"Error reading audio URLs from file: {e}")
        return []

def extract_audio_from_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True
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

def stream_audio(audio_url, looping_video_path, output_url):
    try:
        ffmpeg_command = [
            'ffmpeg',
            '-loglevel', 'info', '-re',
            '-stream_loop', '-1', '-i', looping_video_path,
            '-i', audio_url,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-b:v', '200k', '-maxrate', '200k', '-bufsize', '400k',
            '-r', '15', '-s', '640x360', '-vf', 'format=yuv420p', '-g', '30', '-shortest',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',  # Convert audio to AAC and set sample rate
            '-map', '0:v', '-map', '1:a',
            '-f', 'flv', output_url
        ]
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error streaming audio: {e}")
    except Exception as e:
        print(f"Unexpected error streaming audio: {e}")


def start_streaming(stream_info):
    audio_urls = extract_audio_from_file(stream_info['audio_url_file'])
    if not audio_urls:
        print("Error: No audio URLs found in the file.")
        return
    
    output_url = 'rtmp://a.rtmp.youtube.com/live2/' + stream_info['stream_key']
    looping_video_path = stream_info['looping_video_path']

    while True:
        for audio_url in audio_urls:
            extracted_audio_url = extract_audio_from_url(audio_url)
            if extracted_audio_url is not None:
                stream_audio(extracted_audio_url, looping_video_path, output_url)
            else:
                print(f"Error: Unable to extract audio from {audio_url}")
        
        # Sleep for 1 second before streaming again
        time.sleep(1)

def main():
    # Replace with appropriate values based on your platform and permitted use case
    streaming_info = [
        {
            'stream_key': 'zjjt-2ef6-6mbr-z9qv-1ud9',  # Replace with your platform-specific stream key
            'looping_video_path': 'vid.mp4',  # Replace with the path to your looping video file
            'audio_url_file': 'audio.txt'  # Replace with the path to your audio URL file
        }
    ]

    threads = []
    for info in streaming_info:
        thread = threading.Thread(target=start_streaming, args=(info,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()

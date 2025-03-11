import os
import random
import time
from typing import List, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import yt_dlp
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent
import socket
# import socks  # Removing socks import and usage
from api_key_google import api_key

# Configuration
API_KEY = api_key  # Replace with your API key
DEFAULT_OUTPUT = "youtube_audio"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 60

class YouTubeDownloader:
    def __init__(self, proxy: str = None, cookies_file: str = None):
        self.ua = UserAgent()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'audioformat': 'mp3',
            'audioquality': '192k',
            'outtmpl': os.path.join(DEFAULT_OUTPUT, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'proxy': proxy,
            'socket_timeout': REQUEST_TIMEOUT,
            'http_headers': {'User-Agent': self.ua.random},
            'nocheckcertificate': True,  # Add this line
            'age_limit': 99, # Add this line to bypass age restrictions
            'cookies': cookies_file if cookies_file else None # Add cookies file
        }
        
        # Removing PySocks configuration
        # if proxy:
        #     self._configure_proxy(proxy)

    # Removing _configure_proxy method
    # def _configure_proxy(self, proxy: str):
    #     """Configure proxy for all connections"""
    #     try:
    #         proxy_type, proxy_host, proxy_port = self._parse_proxy(proxy)
    #         socks.set_default_proxy(proxy_type, proxy_host, proxy_port)
    #         socket.socket = socks.socksocket
    #     except Exception as e:
    #         print(f"Error setting up proxy: {e}")

    # Removing _parse_proxy method
    # @staticmethod
    # def _parse_proxy(proxy: str) -> Tuple:
    #     """Parse proxy string"""
    #     parts = proxy.split('://')
    #     proxy_type = parts[0].upper()
    #     host_port = parts[1].split(':')
    #     return {
    #         'SOCKS5': socks.SOCKS5,
    #         'SOCKS4': socks.SOCKS4,
    #         'HTTP': socks.HTTP
    #     }[proxy_type], host_port[0], int(host_port[1])

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1))
    def download_audio(self, url: str) -> str:
        """Download audio with retry"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info and 'title' in info:
                    return os.path.join(DEFAULT_OUTPUT, f"{info['title']}.mp3")
                else:
                    print("Failed to retrieve video information")
                    return None
        except Exception as e:
            print(f"\nDownload error: {str(e)}")
            raise

    def get_channel_videos(self, channel_id: str) -> List[Tuple[str, str]]:
        """Get list of videos via YouTube API"""
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        try:
            channel_info = youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            if not channel_info['items']:
                raise ValueError("Channel not found")
                
            playlist_id = channel_info['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            videos = []
            next_page_token = None

            while True:
                playlist_items = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()

                for item in playlist_items['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    videos.append((
                        item['snippet']['title'],
                        f"https://youtube.com/watch?v={video_id}"
                    ))

                next_page_token = playlist_items.get('nextPageToken')
                if not next_page_token:
                    break

                time.sleep(random.uniform(1, 3))  # Delay between requests

            return videos

        except HttpError as e:
            print(f"API Error: {e.resp.status} {e._get_reason()}")
            return []

def main():
    proxy = input("Enter proxy (optional, format http://ip:port or socks5://ip:port): ") or None  # Updated format description
    channel_id = input("Enter YouTube channel ID: ")
    cookies_file = input("Enter path to cookies file (optional): ") or None

    downloader = YouTubeDownloader(proxy, cookies_file)
    
    if not os.path.exists(DEFAULT_OUTPUT):
        os.makedirs(DEFAULT_OUTPUT)

    try:
        print("\n[1/3] Getting video list...")
        videos = downloader.get_channel_videos(channel_id)
        
        if not videos:
            print("No videos found for download")
            return

        print(f"[2/3] Found {len(videos)} videos. Starting download...")
        
        success = 0
        progress_bar = tqdm(videos, desc="Downloading", unit=" video")
        
        for title, url in progress_bar:
            progress_bar.set_postfix_str(f"Processing: {title[:30]}...")
            
            try:
                time.sleep(random.uniform(2, 10))  # Random delay
                file_path = downloader.download_audio(url)
                if file_path:
                    success += 1
                    tqdm.write(f"Success: {os.path.basename(file_path)}")
                else:
                    tqdm.write(f"Failed to process: {title}")
            except Exception as e:
                tqdm.write(f"Error: {title} - {str(e)}")
                continue

        print(f"\n[3/3] Complete! Successfully downloaded {success}/{len(videos)} audio files")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

if __name__ == "__main__":
    main()

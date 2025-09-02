import asyncio
import os
import re
import json
import glob
import random
import logging
from typing import Union
from urllib.parse import urlparse

import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from .. import app  # Ensure this is the correct import path for your bot

# --------------------- Logging ---------------------
logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=logging.INFO
)

# ------------------ Cookie Handler ------------------
def cookie_txt_file():
    folder_path = f"{os.getcwd()}/cookies"
    filename = f"{os.getcwd()}/cookies/logs.csv"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    with open(filename, 'a') as file:
        file.write(f'Choosen File : {cookie_txt_file}\n')
    return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""

# ----------------- API Functions -------------------
async def get_audio_api(link: str):
    x = re.compile(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
    )
    video_id = x.search(link)
    vidid = video_id.group(1) if video_id else link

    xyz = os.path.join("downloads", f"{vidid}.mp3")
    if os.path.exists(xyz):
        logging.info(f"Audio already exists: {xyz}")
        return xyz

    logging.info(f"Fetching audio from API for video: {vidid}")
    loop = asyncio.get_running_loop()

    def get_url():
        api_url = f"https://nottyboyapii.jaydipmore28.workers.dev/youtube?url=https://youtube.com/watch?v={vidid}&apikey=Nottyboy"
        try:
            logging.info(f"Calling API: {api_url}")
            response = requests.get(api_url).json()
            logging.info(f"API Response: {response}")
            return response.get("mp3")
        except Exception as e:
            logging.error(f"API request failed: {e}")
            return None

    download_url = await loop.run_in_executor(None, get_url)
    if not download_url:
        logging.error("Failed to get audio download URL from API")
        return None

    parsed = urlparse(download_url)
    parts = parsed.path.strip("/").split("/")
    # Simple download via requests
    logging.info(f"Downloading audio from URL: {download_url}")
    r = requests.get(download_url, stream=True)
    with open(xyz, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    logging.info(f"Audio downloaded: {xyz}")
    return xyz

async def get_video_api(link: str):
    x = re.compile(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
    )
    video_id = x.search(link)
    vidid = video_id.group(1) if video_id else link

    xyz = os.path.join("downloads", f"{vidid}.mp4")
    if os.path.exists(xyz):
        logging.info(f"Video already exists: {xyz}")
        return xyz

    logging.info(f"Fetching video from API for video: {vidid}")
    loop = asyncio.get_running_loop()

    def get_url():
        api_url = f"https://nottyboyapii.jaydipmore28.workers.dev/youtube?url=https://youtube.com/watch?v={vidid}&apikey=Nottyboy"
        try:
            logging.info(f"Calling API: {api_url}")
            response = requests.get(api_url).json()
            logging.info(f"API Response: {response}")
            return response.get("mp4")
        except Exception as e:
            logging.error(f"API request failed: {e}")
            return None

    download_url = await loop.run_in_executor(None, get_url)
    if not download_url:
        logging.error("Failed to get video download URL from API")
        return None

    logging.info(f"Downloading video from URL: {download_url}")
    r = requests.get(download_url, stream=True)
    with open(xyz, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    logging.info(f"Video downloaded: {xyz}")
    return xyz

# ----------------- Existing Functions -----------------
async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_txt_file(),
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logging.error(f"yt-dlp Error: {stderr.decode()}")
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        logging.warning("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

# ----------------- YouTubeAPI Class -----------------
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
    ) -> str:
        loop = asyncio.get_running_loop()

        # API-based download
        if songaudio:
            logging.info("Downloading via Audio API...")
            downloaded_file = await get_audio_api(link)
            return downloaded_file, True
        elif songvideo:
            logging.info("Downloading via Video API...")
            downloaded_file = await get_video_api(link)
            return downloaded_file, True

        # Existing yt-dlp logic (fallback)
        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_txt_file(),
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "cookiefile" : cookie_txt_file(),
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        # Fallback for audio/video
        if video:
            downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            downloaded_file = await loop.run_in_executor(None, audio_dl)

        return downloaded_file, True

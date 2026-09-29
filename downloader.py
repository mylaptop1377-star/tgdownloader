import os
import re
import sys
import asyncio
import uuid
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import yt_dlp
import static_ffmpeg

# Make sure ffmpeg and ffprobe are in PATH
try:
    static_ffmpeg.add_paths()
except Exception as e:
    logging.warning(f"Could not initialize static-ffmpeg: {e}")

DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

# Telegram Bot API maksimal fayl hajmi: 50 MB (xavfsiz chegara 49.5 MB)
MAX_TELEGRAM_BYTES = int(49.5 * 1024 * 1024)

def sanitize_filename(name: str) -> str:
    """Fayl nomidagi taqiqlangan belgilarni olib tashlaydi."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()[:120]

def detect_platform(url: str) -> str:
    """Havola qaysi platformaga tegishli ekanligini aniqlaydi."""
    url_lower = url.lower()
    if any(domain in url_lower for domain in ["youtube.com", "youtu.be"]):
        return "youtube"
    elif "instagram.com" in url_lower:
        return "instagram"
    elif any(domain in url_lower for domain in ["facebook.com", "fb.watch", "fb.com"]):
        return "facebook"
    return "unknown"

def get_base_ydl_opts() -> dict:
    """Tezkor yuklash uchun asosiy yt-dlp sozlamalari."""
    return {
        'quiet': True,
        'no_warnings': True,
        'concurrent_fragment_downloads': 8,
        'http_chunk_size': 10 * 1024 * 1024,
        'retries': 5,
        'fragment_retries': 5,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'tv_embedded', 'web'],
            }
        },
    }

COOKIES_FILE = Path(__file__).parent / "youtube_cookies.txt"
RENDER_SECRETS_COOKIE = Path("/etc/secrets/youtube_cookies.txt")

def _get_cookie_path() -> Optional[str]:
    """Render secret file yoki lokal papkadagi cookie faylini topadi."""
    if RENDER_SECRETS_COOKIE.exists():
        return str(RENDER_SECRETS_COOKIE)
    if COOKIES_FILE.exists():
        return str(COOKIES_FILE)
    return None

def _get_yt_base_opts_with_cookies() -> dict:
    """Cookie fayli bilan barqaror YouTube yuklash sozlamalari."""
    opts: dict = {}
    
    cookie_path = _get_cookie_path()
    if cookie_path:
        opts['cookiefile'] = cookie_path
    else:
        opts['extractor_args'] = {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        }

    return opts

def _extract_youtube_info_sync(url: str) -> dict:
    """YouTube video ma'lumotlarini tezkor o'qiydi va taxminiy hajmlarni hisoblaydi."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        **_get_yt_base_opts_with_cookies()
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get('duration', 0)
        formats = info.get('formats', [])
        
        # Audio hajmini aniqlash
        best_audio_size = 0
        for f in formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                size = f.get('filesize') or f.get('filesize_approx') or 0
                if not size and f.get('tbr') and duration:
                    size = int(f['tbr'] * 1000 / 8 * duration)
                if size > best_audio_size:
                    best_audio_size = size

        # Har bir sifat uchun mavjud format va taxminiy hajm
        height_map: Dict[int, dict] = {}
        for f in formats:
            h = f.get('height')
            vcodec = f.get('vcodec', 'none')
            if h and vcodec != 'none':
                # Standart sifatlarga moslash
                target_h = None
                if h >= 1000:
                    target_h = 1080
                elif 650 <= h <= 800:
                    target_h = 720
                elif 400 < h <= 540:
                    target_h = 480
                elif 300 <= h <= 400:
                    target_h = 360
                elif h in [144, 240]:
                    target_h = h

                if target_h:
                    vsize = f.get('filesize') or f.get('filesize_approx') or 0
                    if not vsize and f.get('tbr') and duration:
                        vsize = int(f['tbr'] * 1000 / 8 * duration)
                    total_est = (vsize + best_audio_size) if vsize else 0
                    
                    if target_h not in height_map or (total_est and total_est > height_map[target_h]['size']):
                        height_map[target_h] = {
                            'height': target_h,
                            'size': total_est
                        }

        # Sifatlarni saralash (1080, 720, 480, 360...)
        sorted_heights = sorted(list(height_map.keys()), reverse=True)
        if not sorted_heights:
            sorted_heights = [720, 360]
            height_map = {720: {'height': 720, 'size': 0}, 360: {'height': 360, 'size': 0}}

        qualities = []
        for h in sorted_heights:
            size_bytes = height_map[h]['size']
            size_mb = f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes > 0 else ""
            qualities.append({
                'height': h,
                'label': f"🎬 {h}p" + (f" (~{size_mb})" if size_mb else ""),
                'size_bytes': size_bytes
            })

        audio_mb = f"{best_audio_size / (1024 * 1024):.1f} MB" if best_audio_size > 0 else ""

        return {
            'id': info.get('id', str(uuid.uuid4())[:8]),
            'title': info.get('title', 'YouTube Video'),
            'duration': duration,
            'thumbnail': info.get('thumbnail'),
            'qualities': qualities,
            'audio_label': "🎵 Faqat ovoz (MP3)" + (f" (~{audio_mb})" if audio_mb else ""),
            'url': url
        }

async def get_youtube_info(url: str) -> dict:
    """Asinxron tarzda YouTube ma'lumotlarini olish."""
    return await asyncio.to_thread(_extract_youtube_info_sync, url)

def get_video_duration_ffmpeg(file_path: str) -> float:
    """FFprobe orqali video davomiyligini aniqlaydi."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0

def compress_video_if_needed(file_path: str, duration: int = 0) -> Tuple[str, bool]:
    """Agar video hajmi 49.5 MB dan katta bo'lsa, uni FFmpeg orqali avtomatik siqib,
    Telegram Bot API limitiga (50 MB dan kichik) moslashtiradi."""
    if not os.path.exists(file_path):
        return file_path, False

    current_size = os.path.getsize(file_path)
    if current_size <= MAX_TELEGRAM_BYTES:
        return file_path, False

    logger.info(f"Video hajmi katta ({current_size / (1024*1024):.1f} MB). FFmpeg orqali siqilmoqda...")

    if duration <= 0:
        duration = int(get_video_duration_ffmpeg(file_path))

    if 0 < duration <= 1500:
        target_total_bits = 47.0 * 8 * 1024 * 1024
        target_total_bitrate = int(target_total_bits / duration)
        audio_bitrate = 96000
        video_bitrate = max(180000, target_total_bitrate - audio_bitrate)
    else:
        video_bitrate = 450000
        audio_bitrate = 96000

    compressed_path = file_path.replace(".mp4", "_compressed.mp4")
    if compressed_path == file_path:
        compressed_path = f"{file_path}_comp.mp4"

    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-c:v", "libx264",
        "-b:v", str(video_bitrate),
        "-maxrate", str(int(video_bitrate * 1.3)),
        "-bufsize", str(int(video_bitrate * 2)),
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", f"{audio_bitrate // 1000}k",
        "-movflags", "+faststart",
        compressed_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(compressed_path) and os.path.getsize(compressed_path) > 0:
            new_size = os.path.getsize(compressed_path)
            logger.info(f"Siqish yakunlandi: {new_size / (1024*1024):.1f} MB")
            try:
                os.remove(file_path)
            except Exception:
                pass
            return compressed_path, True
    except Exception as e:
        logger.error(f"Videoni siqishda xatolik: {e}")

    return file_path, False

def _download_youtube_video_sync(url: str, height: int) -> dict:
    """YouTube videosini tanlangan sifatda tezkor yuklaydi."""
    file_id = str(uuid.uuid4())[:8]
    output_template = str(DOWNLOAD_DIR / f"yt_{file_id}_{height}p.%(ext)s")

    format_selector = (
        f"bestvideo[height<={height}][vcodec^=avc]+bestaudio[acodec^=mp4a]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]/"
        f"bestvideo+bestaudio/"
        f"best"
    )

    base = get_base_ydl_opts()
    base.update(_get_yt_base_opts_with_cookies())
    base.update({
        'format': format_selector,
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
    })
    ydl_opts = base

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        expected_mp4 = f"{base}.mp4"
        final_path = expected_mp4 if os.path.exists(expected_mp4) else filename

        duration = info.get('duration', 0)
        final_path, compressed = compress_video_if_needed(final_path, duration)
        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        return {
            'file_path': final_path,
            'title': info.get('title', 'YouTube Video'),
            'duration': duration,
            'size': file_size,
            'compressed': compressed
        }

async def download_youtube_video(url: str, height: int) -> dict:
    return await asyncio.to_thread(_download_youtube_video_sync, url, height)

def _download_youtube_audio_sync(url: str) -> dict:
    """YouTube videosidan faqat ovozni (MP3) tezkor ajratib yuklaydi."""
    file_id = str(uuid.uuid4())[:8]
    output_template = str(DOWNLOAD_DIR / f"yt_audio_{file_id}.%(ext)s")

    base = get_base_ydl_opts()
    base.update(_get_yt_base_opts_with_cookies())
    base.update({
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    })
    ydl_opts = base

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        mp3_path = f"{base}.mp3"
        final_path = mp3_path if os.path.exists(mp3_path) else filename

        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        return {
            'file_path': final_path,
            'title': info.get('title', 'Audio'),
            'duration': info.get('duration', 0),
            'size': file_size
        }

async def download_youtube_audio(url: str) -> dict:
    return await asyncio.to_thread(_download_youtube_audio_sync, url)

def _download_instagram_sync(url: str) -> dict:
    """Instagram (reel, post, carousel, video) - barcha turlarni download qiladi."""
    work_dir = DOWNLOAD_DIR / f"insta_{uuid.uuid4().hex[:8]}"
    work_dir.mkdir(exist_ok=True, parents=True)

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        'quiet': False,
        'no_warnings': False,
        'format': 'best',
        'outtmpl': str(work_dir / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'noplaylist': False,
        'extract_flat': False,
    })

    media_items = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # Entries (carousel) yoki single video
        entries = info_dict.get('entries', [info_dict]) if isinstance(info_dict, dict) else [info_dict]

        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue

            title = sanitize_filename(entry.get('title', f'instagram_{idx+1}'))
            is_video = entry.get('ext') in ['mp4', 'mkv', 'mov', 'avi']

            # Faylni papkada topish
            found_file = None
            for file_path in work_dir.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    found_file = str(file_path)
                    break

            if found_file:
                duration = entry.get('duration', 0)
                if is_video:
                    found_file, _ = compress_video_if_needed(found_file, duration)

                media_items.append({
                    'type': 'video' if is_video else 'photo',
                    'file_path': found_file,
                    'title': title,
                    'index': idx + 1,
                    'total': len(entries)
                })

    except Exception as e:
        logger.error(f"Instagram download xatolik: {e}")
        # Hattoki xato bo'lsa, topilgan fayllarni qaytarish

    if not media_items:
        raise Exception("Instagram dan fayl topilmadi")

    return {
        'files': media_items,
        'total': len(media_items),
        'is_carousel': len(media_items) > 1,
        'work_dir': str(work_dir)
    }

async def download_instagram(url: str) -> dict:
    return await asyncio.to_thread(_download_instagram_sync, url)

def _download_facebook_sync(url: str) -> dict:
    """Facebook videosini yuklaydi."""
    file_id = str(uuid.uuid4())[:8]
    output_template = str(DOWNLOAD_DIR / f"fb_{file_id}.%(ext)s")

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
    })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info and info['entries']:
            info = info['entries'][0]

        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        expected_mp4 = f"{base}.mp4"
        final_path = expected_mp4 if os.path.exists(expected_mp4) else filename

        duration = info.get('duration', 0)
        final_path, compressed = compress_video_if_needed(final_path, duration)
        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        return {
            'file_path': final_path,
            'title': info.get('title', 'Video'),
            'duration': duration,
            'size': file_size,
            'compressed': compressed
        }

async def download_facebook(url: str) -> dict:
    return await asyncio.to_thread(_download_facebook_sync, url)

def cleanup_file(file_path: str):
    """Vaqtinchalik yuklangan faylni o'chiradi."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"O'chirildi: {file_path}")
    except Exception as e:
        logger.error(f"Faylni o'chirishda xatolik: {e}")

def cleanup_directory(dir_path: str):
    """Vaqtinchalik yuklangan qo'lni o'chiradi."""
    try:
        if dir_path and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            logger.info(f"Qo'l o'chirildi: {dir_path}")
    except Exception as e:
        logger.error(f"Qo'lni o'chirishda xatolik: {e}")

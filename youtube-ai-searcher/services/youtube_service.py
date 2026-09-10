import os
import re
import uuid
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse
import yt_dlp


def extract_video_id(url: str) -> Optional[str]:
    """
    다양한 형태의 YouTube URL에서 11자리 Video ID를 추출합니다.
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    if not url:
        return None
    
    url = url.strip()
    
    # 11자리 단독 ID가 들어온 경우
    if len(url) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url

    parsed = urlparse(url)
    
    # youtu.be/VIDEO_ID
    if "youtu.be" in parsed.netloc:
        path = parsed.path.lstrip("/")
        return path.split("/")[0].split("?")[0]
        
    # youtube.com/watch?v=VIDEO_ID
    if "youtube.com" in parsed.netloc or "m.youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            if "v" in query:
                return query["v"][0]
        elif parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2].split("?")[0]
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2].split("?")[0]

    # 정규식 패턴 매칭
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if match:
        return match.group(1)

    return None


def format_duration(seconds: Optional[int]) -> str:
    """초 단위 시간을 MM:SS 또는 HH:MM:SS 형식으로 변환합니다."""
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_video_info(url: str) -> Dict[str, Any]:
    """
    YouTube 영상 메타데이터(제목, 채널, 길이, 썸네일 등)를 추출합니다.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("유효하지 않은 YouTube URL입니다.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_url, download=False)
        if not info:
            raise ValueError("영상 정보를 불러올 수 없습니다.")

        return {
            "video_id": video_id,
            "title": info.get("title", "제목 없음"),
            "uploader": info.get("uploader", "알 수 없음"),
            "channel": info.get("channel", info.get("uploader", "알 수 없음")),
            "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
            "duration": info.get("duration", 0),
            "duration_formatted": format_duration(info.get("duration", 0)),
            "view_count": info.get("view_count", 0),
            "webpage_url": clean_url,
        }


def download_audio(url: str, output_dir: str) -> Dict[str, Any]:
    """
    Gemini STT 분석을 위해 YouTube 영상의 오디오를 다운로드합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("유효하지 않은 YouTube URL입니다.")

    unique_id = str(uuid.uuid4())[:8]
    out_template = os.path.join(output_dir, f"{video_id}_{unique_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
    }

    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_url, download=True)
        if not info:
            raise ValueError("오디오 다운로드에 실패했습니다.")

        downloaded_file = ydl.prepare_filename(info)
        
        # 실제 생성된 파일 확인
        if not os.path.exists(downloaded_file):
            base_path = os.path.splitext(downloaded_file)[0]
            for ext in [".m4a", ".webm", ".opus", ".mp3", ".wav", ".aac"]:
                candidate = base_path + ext
                if os.path.exists(candidate):
                    downloaded_file = candidate
                    break

        if not os.path.exists(downloaded_file):
            raise FileNotFoundError(f"다운로드된 오디오 파일을 찾을 수 없습니다: {downloaded_file}")

        file_size = os.path.getsize(downloaded_file)
        ext = os.path.splitext(downloaded_file)[1].lower().lstrip(".")

        mime_map = {
            "m4a": "audio/mp4",
            "mp4": "audio/mp4",
            "mp3": "audio/mp3",
            "wav": "audio/wav",
            "webm": "audio/webm",
            "opus": "audio/ogg",
            "ogg": "audio/ogg",
        }
        mime_type = mime_map.get(ext, "audio/mp4")

        return {
            "video_id": video_id,
            "file_path": downloaded_file,
            "filename": os.path.basename(downloaded_file),
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "mime_type": mime_type,
            "title": info.get("title", "제목 없음"),
            "uploader": info.get("uploader", "알 수 없음"),
            "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
            "duration": info.get("duration", 0),
            "duration_formatted": format_duration(info.get("duration", 0)),
        }

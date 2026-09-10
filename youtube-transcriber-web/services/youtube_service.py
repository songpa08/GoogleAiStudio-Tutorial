import os
import re
import uuid
from typing import Any, Dict, Optional
import yt_dlp


def sanitize_filename(name: str) -> str:
    """파일명으로 사용할 수 없는 특수문자를 제거합니다."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def format_duration(seconds: Optional[int]) -> str:
    """초 단위 시간을 HH:MM:SS 또는 MM:SS 형식으로 변환합니다."""
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_video_info(url: str) -> Dict[str, Any]:
    """
    유튜브 URL에서 영상 메타데이터(제목, 썸네일, 길이 등)를 추출합니다.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("영상 정보를 가져올 수 없습니다.")

        return {
            "id": info.get("id", ""),
            "title": info.get("title", "제목 없음"),
            "uploader": info.get("uploader", "알 수 없음"),
            "channel": info.get("channel", info.get("uploader", "알 수 없음")),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "duration_formatted": format_duration(info.get("duration", 0)),
            "view_count": info.get("view_count", 0),
            "webpage_url": info.get("webpage_url", url),
        }


def download_audio(url: str, output_dir: str) -> Dict[str, Any]:
    """
    유튜브 영상의 오디오 스트림을 다운로드합니다.
    ffmpeg 유무에 관계없이 동작하도록 m4a 또는 원본 최적 오디오를 추출합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    unique_id = str(uuid.uuid4())[:8]
    out_template = os.path.join(output_dir, f"%(id)s_{unique_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("오디오 다운로드에 실패했습니다.")

        # 다운로드된 파일 경로 탐색
        downloaded_file = ydl.prepare_filename(info)
        
        # 파일이 실제로 존재하는지 확인 (확장자가 달라질 수 있음)
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

        # MIME 타입 결정
        mime_map = {
            "m4a": "audio/mp4",
            "mp4": "audio/mp4",
            "mp3": "audio/mp3",
            "wav": "audio/wav",
            "webm": "audio/webm",
            "opus": "audio/ogg",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "aac": "audio/aac",
        }
        mime_type = mime_map.get(ext, "audio/mp4")

        return {
            "file_path": downloaded_file,
            "filename": os.path.basename(downloaded_file),
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "mime_type": mime_type,
            "title": info.get("title", "제목 없음"),
            "uploader": info.get("uploader", "알 수 없음"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "duration_formatted": format_duration(info.get("duration", 0)),
        }

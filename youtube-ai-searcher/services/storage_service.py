import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from services.youtube_service import extract_video_id

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "youtube_transcripts.csv"

CSV_HEADERS = [
    "video_id",
    "url",
    "title",
    "uploader",
    "duration",
    "duration_formatted",
    "thumbnail",
    "file_size_mb",
    "summary",
    "full_content",
    "segments_json",
    "created_at",
]


def init_storage(csv_path: Optional[Path] = None) -> Path:
    """CSV 저장소 디렉터리 및 헤더 파일을 초기화합니다."""
    path = csv_path or DEFAULT_CSV_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
    return path


def get_cached_transcript(url: str, csv_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    동일한 YouTube URL(또는 Video ID)로 저장된 기존 트랜스크립트가 있는지 확인하고 반환합니다.
    """
    path = init_storage(csv_path)
    video_id = extract_video_id(url)
    if not video_id:
        return None

    if not path.exists():
        return None

    with open(path, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("video_id") == video_id or row.get("url") == url:
                try:
                    segments = json.loads(row.get("segments_json", "[]"))
                except Exception:
                    segments = []

                return {
                    "cached": True,
                    "created_at": row.get("created_at"),
                    "video": {
                        "video_id": row.get("video_id"),
                        "title": row.get("title"),
                        "uploader": row.get("uploader"),
                        "thumbnail": row.get("thumbnail"),
                        "duration": int(row.get("duration", 0)) if row.get("duration") else 0,
                        "duration_formatted": row.get("duration_formatted"),
                        "file_size_mb": float(row.get("file_size_mb", 0.0)) if row.get("file_size_mb") else 0.0,
                        "embed_url": f"https://www.youtube.com/embed/{row.get('video_id')}?enablejsapi=1",
                    },
                    "transcription": {
                        "model_used": "cached-from-csv",
                        "summary": row.get("summary", ""),
                        "full_content": row.get("full_content", ""),
                        "full_transcript": row.get("full_content", ""),
                        "segments": segments,
                    },
                }

    return None


def save_transcript(
    url: str,
    video_data: Dict[str, Any],
    transcription_data: Dict[str, Any],
    csv_path: Optional[Path] = None,
) -> None:
    """
    새롭게 추출된 영상 정보와 트랜스크립트 데이터를 CSV 파일에 추가/갱신 저장합니다.
    """
    path = init_storage(csv_path)
    video_id = video_data.get("video_id") or extract_video_id(url)
    if not video_id:
        return

    # 기존에 같은 video_id가 있으면 최신으로 갱신하기 위해 전체 행 읽기
    existing_rows = []
    found = False

    if path.exists():
        with open(path, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("video_id") == video_id:
                    found = True
                    # 갱신될 데이터로 대체
                    existing_rows.append({
                        "video_id": video_id,
                        "url": url,
                        "title": video_data.get("title", ""),
                        "uploader": video_data.get("uploader", ""),
                        "duration": video_data.get("duration", 0),
                        "duration_formatted": video_data.get("duration_formatted", ""),
                        "thumbnail": video_data.get("thumbnail", ""),
                        "file_size_mb": video_data.get("file_size_mb", 0.0),
                        "summary": transcription_data.get("summary", ""),
                        "full_content": transcription_data.get("full_content", ""),
                        "segments_json": json.dumps(transcription_data.get("segments", []), ensure_ascii=False),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })
                else:
                    existing_rows.append(row)

    if not found:
        existing_rows.append({
            "video_id": video_id,
            "url": url,
            "title": video_data.get("title", ""),
            "uploader": video_data.get("uploader", ""),
            "duration": video_data.get("duration", 0),
            "duration_formatted": video_data.get("duration_formatted", ""),
            "thumbnail": video_data.get("thumbnail", ""),
            "file_size_mb": video_data.get("file_size_mb", 0.0),
            "summary": transcription_data.get("summary", ""),
            "full_content": transcription_data.get("full_content", ""),
            "segments_json": json.dumps(transcription_data.get("segments", []), ensure_ascii=False),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"[Storage Service] CSV 저장 완료 ({path}): {video_id} - {video_data.get('title')}")

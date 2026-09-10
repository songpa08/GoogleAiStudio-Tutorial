import os
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from services.youtube_service import get_video_info, download_audio
from services.gemini_stt_service import transcribe_audio_with_gemini

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="YouTube Audio Transcriber & Gemini STT",
    description="유튜브 영상 오디오 다운로드 및 Gemini AI 음성 전사 웹 서비스",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 마운트
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# 요청 Pydantic 모델
class VideoInfoRequest(BaseModel):
    url: str


class TranscribeRequest(BaseModel):
    url: str
    api_key: Optional[str] = None
    model: Optional[str] = "gemini-2.5-flash"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 대시보드 페이지"""
    has_env_key = bool(os.environ.get("GEMINI_API_KEY"))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "has_env_key": has_env_key,
        },
    )


@app.post("/api/video-info")
async def api_get_video_info(req: VideoInfoRequest):
    """유튜브 영상 메타데이터(썸네일, 제목 등) 조회"""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해주세요.")

    try:
        info = get_video_info(url)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"영상 정보 조회 실패: {str(e)}")


@app.post("/api/transcribe")
async def api_transcribe_video(req: TranscribeRequest):
    """유튜브 오디오 다운로드 및 Gemini 음성 전사 실행"""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해주세요.")

    api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY가 필요합니다. 상단 설정에서 API 키를 입력하거나 환경 변수에 등록해주세요.",
        )

    try:
        # 1. 오디오 다운로드
        audio_info = download_audio(url, str(DOWNLOADS_DIR))
        audio_path = audio_info["file_path"]
        mime_type = audio_info["mime_type"]

        # 2. Gemini STT 전사 및 분석
        stt_result = transcribe_audio_with_gemini(
            audio_path=audio_path,
            mime_type=mime_type,
            api_key=api_key,
            model_name=req.model or "gemini-2.5-flash",
        )

        # 웹에서 재생할 수 있는 오디오 스트리밍 URL
        audio_url = f"/api/audio/{audio_info['filename']}"

        return {
            "success": True,
            "video": {
                "title": audio_info.get("title"),
                "uploader": audio_info.get("uploader"),
                "thumbnail": audio_info.get("thumbnail"),
                "duration": audio_info.get("duration"),
                "duration_formatted": audio_info.get("duration_formatted"),
                "file_size_mb": audio_info.get("file_size_mb"),
                "audio_url": audio_url,
                "audio_filename": audio_info["filename"],
            },
            "transcription": stt_result,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")


@app.get("/api/audio/{filename}")
async def get_audio_stream(filename: str):
    """다운로드된 오디오 스트리밍/재생"""
    # 디렉터리 순회 방지 (Path Traversal Protection)
    safe_name = os.path.basename(filename)
    file_path = DOWNLOADS_DIR / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")

    ext = file_path.suffix.lower()
    media_types = {
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".mp3": "audio/mp3",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=safe_name,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

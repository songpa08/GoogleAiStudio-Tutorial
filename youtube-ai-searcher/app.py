import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from services.youtube_service import get_video_info, download_audio, extract_video_id
from services.stt_service import transcribe_audio_gemini_35
from services.qa_service import answer_video_question
from services.storage_service import get_cached_transcript, save_transcript, DEFAULT_CSV_PATH
from fastapi.responses import HTMLResponse, Response, FileResponse

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI YouTube Searcher",
    description="YouTube 스타일 AI 영상 검색기 및 Gemini 3.5 STT & Gemini 3.8 Q&A",
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Pydantic 요청 스키마
class ProcessVideoRequest(BaseModel):
    url: str
    api_key: Optional[str] = None
    stt_model: Optional[str] = "gemini-3.7-flash"


class ChatRequest(BaseModel):
    question: str
    video_title: str
    transcript_text: str
    api_key: Optional[str] = None
    qa_model: Optional[str] = "gemini-3.8-flash"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """YouTube 스타일 메인 대시보드 페이지"""
    has_env_key = bool(os.environ.get("GEMINI_API_KEY"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "has_env_key": has_env_key,
        },
    )


@app.post("/api/process")
async def api_process_video(req: ProcessVideoRequest):
    """
    유튜브 URL을 받아 기존 CSV 저장소에 저장된 트랜스크립트가 있는지 먼저 확인하고,
    있다면 저장된 데이터를 즉시 반환하며,
    없다면 오디오를 다운로드하여 Gemini STT로 추출한 뒤 CSV 파일에 저장합니다.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 영상 링크(URL)를 입력해주세요.")

    # 1. 기존 CSV 캐시 확인 (2번째 호출부터는 즉시 반환)
    cached_result = get_cached_transcript(url)
    if cached_result:
        print(f"[API] CSV 캐시 발견: {url} -> 저장된 트랜스크립트 즉시 반환")
        return {
            "success": True,
            "from_cache": True,
            "created_at": cached_result.get("created_at"),
            "video": cached_result["video"],
            "transcription": cached_result["transcription"],
        }

    # 2. 캐시가 없으면 Gemini API 키 확인 후 신규 추출
    api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY가 필요합니다. 환경 변수를 설정하거나 우측 상단 키 설정창에 입력해주세요.",
        )

    try:
        # 3. 유튜브 Video ID 파싱
        video_id = extract_video_id(url)
        if not video_id:
            raise HTTPException(status_code=400, detail="유효한 YouTube URL이 아닙니다.")

        # 4. 오디오 다운로드
        audio_info = download_audio(url, str(DOWNLOADS_DIR))

        # 5. Gemini STT 실행
        stt_result = transcribe_audio_gemini_35(
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            api_key=api_key,
            model_name=req.stt_model or "gemini-3.7-flash",
        )

        video_payload = {
            "video_id": video_id,
            "title": audio_info.get("title"),
            "uploader": audio_info.get("uploader"),
            "thumbnail": audio_info.get("thumbnail"),
            "duration": audio_info.get("duration"),
            "duration_formatted": audio_info.get("duration_formatted"),
            "file_size_mb": audio_info.get("file_size_mb"),
            "embed_url": f"https://www.youtube.com/embed/{video_id}?enablejsapi=1",
        }

        # 6. CSV 파일에 저장 (영구 보관 및 캐싱)
        try:
            save_transcript(
                url=url,
                video_data=video_payload,
                transcription_data=stt_result,
            )
        except Exception as save_err:
            print(f"[API Warning] CSV 저장 중 오류: {save_err}")

        return {
            "success": True,
            "from_cache": False,
            "video": video_payload,
            "transcription": stt_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"영상 처리 중 오류 발생: {str(e)}")


@app.get("/api/export-csv")
async def api_export_csv():
    """저장된 전체 유튜브 트랜스크립트 CSV 파일을 다운로드합니다."""
    if not DEFAULT_CSV_PATH.exists():
        raise HTTPException(status_code=404, detail="저장된 트랜스크립트 CSV 파일이 없습니다.")
    return FileResponse(
        path=str(DEFAULT_CSV_PATH),
        filename="youtube_transcripts.csv",
        media_type="text/csv",
    )


@app.post("/api/chat")
async def api_chat_with_video(req: ChatRequest):
    """
    추출된 트랜스크립트와 영상을 바탕으로 Gemini 3.8 Flash를 호출하여 질의응답을 수행합니다.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")

    api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 필요합니다.")

    try:
        res = answer_video_question(
            question=question,
            video_title=req.video_title,
            transcript_text=req.transcript_text,
            api_key=api_key,
            model_name=req.qa_model or "gemini-3.8-flash",
        )
        return {"success": True, "data": res}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"답변 생성 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)

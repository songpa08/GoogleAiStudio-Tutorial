# 🎙️ YouTube Audio Transcriber & Gemini STT Web Service

유튜브 영상 URL을 입력하면 고음질 오디오를 다운로드하고, Google Gemini AI를 통해 **자막/텍스트 전사(STT), 화자 분리, 타임스탬프 및 3줄 핵심 요약**을 제공하는 웹 애플리케이션입니다.

---

## ✨ 주요 기능

1. **유튜브 오디오 다운로드 (`yt-dlp`)**:
   - 영상 링크만으로 최적의 오디오 스트림(m4a/webm/mp3) 자동 추출
   - 영상 제목, 채널명, 썸네일, 재생 시간 메타데이터 표시
2. **Google Gemini 멀티모달 오디오 STT (`google-genai`)**:
   - `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.5-transcribe` 모델 지원
   - 타임스탬프(`[MM:SS]`) 및 화자 분리(Diarization)
   - 💡 한 줄 요약 및 핵심 포인트 불릿 정리
3. **사용자 친화적 모던 웹 UI**:
   - 내장 오디오 플레이어를 통한 전사 오디오 재생
   - 탭 구분: **핵심 요약** / **타임스탬프 & 대화** / **전체 전문**
   - 원클릭 클립보드 복사
   - **TXT**, **Markdown (.md)**, **자막 (.srt)** 파일 다운로드 지원

---

## 🚀 빠른 시작 가이드

### 1. 가상환경 및 의존성 패키지 설치

```bash
cd youtube-transcriber-web
pip install -r requirements.txt
```

### 2. Gemini API 키 설정

API 키를 환경 변수로 등록하거나, 웹 페이지 상단의 입력 필드에 직접 입력할 수 있습니다.

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Windows CMD
set GEMINI_API_KEY=your_api_key_here

# Linux / macOS
export GEMINI_API_KEY="your_api_key_here"
```

### 3. 웹 서버 실행

```bash
python app.py
```
또는
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

실행 후 브라우저에서 **`http://localhost:8000`** 또는 **`http://127.0.0.1:8000`** 에 접속합니다.

---

## 📁 디렉터리 구조

```text
youtube-transcriber-web/
├── app.py                      # FastAPI 백엔드 메인 서버
├── services/
│   ├── __init__.py
│   ├── youtube_service.py      # yt-dlp 기반 유튜브 정보 추출 및 오디오 다운로드
│   └── gemini_stt_service.py   # Gemini API 기반 음성 전사 및 구조화 분석
├── templates/
│   └── index.html              # Tailwind CSS 기반 반응형 대시보드
├── static/
│   ├── css/style.css           # 커스텀 스타일 및 스크롤바/플레이어 서식
│   └── js/app.js               # 비동기 전사 요청, 상태 관리, 다운로드 로직
├── downloads/                  # 다운로드된 임시 오디오 저장 경로
├── requirements.txt            # 필요 패키지 목록
└── README.md                   # 서비스 매뉴얼
```

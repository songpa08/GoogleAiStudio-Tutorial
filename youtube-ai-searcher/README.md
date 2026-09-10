# 🎬 AI 유튜브 검색기 (AI YouTube Searcher)

YouTube 스타일의 모던 UI에서 영상을 시청하면서, **Gemini 3.5 Transcribe**로 추출한 자막을 검색해 해당 위치로 바로 이동(`seekTo`)하고, **Gemini 3.8 Flash**로 영상 내용에 대해 실시간 Q&A를 나눌 수 있는 웹 서비스입니다.

---

## ✨ 주요 기능

1. **YouTube 스타일 직관적 UI**:
   - 상단 헤더: YouTube 시그니처 검색창 (URL 입력 후 돋보기 버튼 또는 Enter)
   - 불필요한 마이크/만들기/알림 버튼은 제거하고 깔끔한 다크 테마 레이아웃 제공
2. **YouTube IFrame Player 연동**:
   - 고화질 영상 재생 및 일시정지, 10초 앞/뒤 탐색
   - **음향 크기(볼륨 0~100%) 조절 슬라이더** 및 원클릭 음소거 기능
3. **Gemini 3.5 Transcribe 기반 정밀 STT**:
   - `yt-dlp`로 오디오를 다운로드한 후 `gemini-3.5-transcribe` 모델을 통해 타임스탬프와 대화 자막 추출
   - 💡 3줄 핵심 요약 자동 생성
4. **인터랙티브 타임점프(Seek & Play) & 실시간 자막 검색**:
   - 자막 목록에서 특정 키워드/대사 실시간 필터 검색
   - 타임스탬프 배지(`[00:15]`)를 클릭하면 영상이 해당 위치로 즉시 이동하여 재생
   - 영상 재생 시간에 맞춰 현재 대화 문장 자동 하이라이트
5. **Gemini 3.8 Flash 영상 Q&A 챗봇**:
   - 전사된 영상 컨텍스트를 기반으로 궁금한 점을 질문하면 정확한 타임스탬프 링크와 함께 답변

---

## 🚀 실행 방법

### 1. 가상환경 활성화

```powershell
conda activate myenv
```

### 2. 디렉터리 이동 및 실행

```powershell
cd "c:\Users\yunjo\Desktop\AI Agent\projet\GoogleAiStudio-Tutorial\youtube-ai-searcher"
python app.py
```
또는
```powershell
uvicorn app:app --port 8001 --reload
```

### 3. 브라우저 접속

웹 브라우저에서 **`http://localhost:8001`** 또는 **`http://127.0.0.1:8001`** 에 접속합니다.

---

## 📁 디렉터리 구조

```text
youtube-ai-searcher/
├── app.py                      # FastAPI 메인 웹 서버 & 라우트
├── services/
│   ├── __init__.py
│   ├── youtube_service.py      # yt-dlp 기반 유튜브 정보 및 오디오 추출
│   ├── stt_service.py          # Gemini 3.5 Transcribe 기반 정밀 STT
│   └── qa_service.py           # Gemini 3.8 Flash 기반 영상 Q&A
├── templates/
│   └── index.html              # YouTube 스타일 반응형 웹 UI
├── static/
│   ├── css/youtube_theme.css   # YouTube Dark 테마 커스텀 스타일
│   └── js/player_app.js        # YouTube IFrame API 연동, 자막 검색, 볼륨, Q&A 로직
├── downloads/                  # 오디오 임시 저장소
├── requirements.txt            # 의존성 패키지 목록
└── README.md                   # 서비스 설명서
```

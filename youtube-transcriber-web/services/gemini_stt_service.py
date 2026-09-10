import os
import time
from typing import Any, Dict, Optional
from google import genai
from google.genai import types


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """Gemini 클라이언트를 생성합니다."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. 환경 변수 또는 화면에서 API 키를 입력해주세요.")
    return genai.Client(api_key=key)


def transcribe_audio_with_gemini(
    audio_path: str,
    mime_type: str = "audio/mp4",
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    include_summary: bool = True,
    language_hint: str = "한국어",
) -> Dict[str, Any]:
    """
    Gemini API를 사용하여 오디오 파일에서 텍스트 전사, 타임스탬프, 화자 분리 및 요약을 수행합니다.
    """
    client = get_gemini_client(api_key)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    # 1. 파일 업로드 (GenAI Files API 활용으로 대용량 오디오도 안정적 처리)
    print(f"[Gemini STT] 오디오 파일 업로드 중: {audio_path}")
    uploaded_file = client.files.upload(
        file=audio_path,
        mime_type=mime_type,
    )

    # 업로드 파일 활성화 대기 (필요 시)
    while uploaded_file.state.name == "PROCESSING":
        print("[Gemini STT] 파일 처리 대기 중...")
        time.sleep(1)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise RuntimeError("Google GenAI 파일 처리에 실패했습니다.")

    try:
        # 2. 전사 및 구조화 프롬프트 작성
        system_instruction = (
            "당신은 최고 수준의 음성 인식(STT) 및 오디오 분석 전문가입니다. "
            "주어진 오디오를 듣고 오디오의 언어(주로 한국어/영어)에 맞춰 정확하게 받아쓰고 분석하세요."
        )

        prompt = f"""
이 오디오 파일의 음성을 주의 깊게 듣고 다음 형식에 맞춰 한국어로 자세하고 정확하게 전사 및 분석을 제공해주세요.

---

### [1] 💡 핵심 요약 및 주요 포인트
- **한 줄 요약**: (영상의 핵심 주제를 1문장으로 요약)
- **주요 내용 (Key Points)**:
  - 3~5개의 핵심 요약 불릿 포인트 작성

### [2] ⏱️ 타임스탬프 및 화자별 대화 (Timestamped & Diarized Transcript)
- 각 발화 구간별 대략적인 시간([MM:SS])과 화자(화자 1, 화자 2 또는 발화자 이름/역할)를 구분하여 대화 형식으로 기록하세요.
- 예시:
  - **[00:00] 화자 1**: 안녕하세요, 오늘 다룰 주제는...
  - **[00:15] 화자 2**: 네, 정말 기대되네요.

### [3] 📝 전체 전문 (Full Transcript)
- 단락별로 읽기 쉽게 정리된 전체 전사 텍스트를 작성하세요.

---
정확하고 누락 없이 충실하게 작성해주세요.
"""

        print(f"[Gemini STT] {model_name} 모델을 통한 전사 생성 중...")
        response = client.models.generate_content(
            model=model_name,
            contents=[
                uploaded_file,
                types.Part.from_text(text=prompt),
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,  # 사실적이고 정확한 전사를 위해 낮은 temperature 사용
            ),
        )

        full_text = response.text or ""

        # 3. 마크다운 결과물 파싱 (섹션별 분리)
        summary_section = ""
        timestamp_section = ""
        raw_transcript_section = ""

        # 섹션 구분
        if "### [1] 💡 핵심 요약" in full_text:
            parts = full_text.split("### [1] 💡 핵심 요약")
            rest = parts[1] if len(parts) > 1 else ""

            if "### [2] ⏱️ 타임스탬프" in rest:
                p2 = rest.split("### [2] ⏱️ 타임스탬프")
                summary_section = p2[0].strip().lstrip("및 주요 포인트").strip()
                rest2 = p2[1]

                if "### [3] 📝 전체 전문" in rest2:
                    p3 = rest2.split("### [3] 📝 전체 전문")
                    timestamp_section = p3[0].strip().lstrip("및 화자별 대화 (Timestamped & Diarized Transcript)").strip()
                    raw_transcript_section = p3[1].strip().lstrip("(Full Transcript)").strip()
                else:
                    timestamp_section = rest2.strip()
            else:
                summary_section = rest.strip()
        
        # 파싱 실패 시 기본 전체 텍스트 할당
        if not summary_section and not timestamp_section and not raw_transcript_section:
            raw_transcript_section = full_text

        return {
            "model_used": model_name,
            "full_content": full_text,
            "summary": summary_section,
            "timestamps": timestamp_section,
            "transcript": raw_transcript_section or full_text,
        }

    finally:
        # 4. 임시 업로드 파일 정리
        try:
            client.files.delete(name=uploaded_file.name)
            print(f"[Gemini STT] 원격 임시 파일 정리 완료: {uploaded_file.name}")
        except Exception as e:
            print(f"[Gemini STT] 원격 임시 파일 삭제 중 경고: {e}")

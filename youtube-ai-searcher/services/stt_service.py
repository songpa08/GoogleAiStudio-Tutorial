import os
import re
import time
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types


def parse_timestamp_to_seconds(ts_str: str) -> int:
    """[MM:SS] 또는 [HH:MM:SS] 형식의 문자열을 초(seconds) 단위 정수로 변환합니다."""
    ts_clean = re.sub(r"[^\d:]", "", ts_str)
    parts = ts_clean.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        pass
    return 0


def parse_transcript_segments(text: str) -> List[Dict[str, Any]]:
    """
    STT 전사 텍스트에서 타임스탬프가 포함된 라인들을 정밀 파싱하여 세그먼트 리스트로 변환합니다.
    다양한 포맷 지원:
    - **[00:15] 화자 1**: 대화 내용
    - - [00:15] 이름: 내용
    - [00:15] 내용
    """
    segments = []
    lines = text.split("\n")

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # [MM:SS] 또는 [H:MM:SS] 또는 [HH:MM:SS] 패턴 검색 (마크다운 ** 무시)
        match = re.search(r"\[?(\b\d{1,2}:\d{2}(?::\d{2})?\b)\]?", line_clean)
        if match:
            raw_ts = match.group(1)
            seconds = parse_timestamp_to_seconds(raw_ts)

            # 타임스탬프 이후 텍스트 분리
            after_ts = line_clean[match.end():].strip().lstrip("] :*-").strip()

            speaker = "화자"
            dialogue_text = after_ts

            # 화자 분리 시도: "**화자 이름**: 대화" 또는 "화자 이름: 대화"
            sp_match = re.match(r"^\*{0,2}([^:*_]{1,20})\*{0,2}[:：]\s*(.*)$", after_ts)
            if sp_match:
                speaker = sp_match.group(1).strip().strip("*_")
                dialogue_text = sp_match.group(2).strip()
            elif not dialogue_text:
                # 타임스탬프 이전 텍스트가 있을 경우
                before_ts = line_clean[:match.start()].strip().lstrip("*- ").strip()
                if before_ts:
                    dialogue_text = before_ts

            if dialogue_text:
                segments.append({
                    "timestamp": raw_ts if ":" in raw_ts else f"00:{raw_ts}",
                    "seconds": seconds,
                    "speaker": speaker,
                    "text": dialogue_text,
                    "raw_line": line_clean,
                })

    return segments


def transcribe_audio_gemini_35(
    audio_path: str,
    mime_type: str = "audio/mp4",
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.7-flash",
) -> Dict[str, Any]:
    """
    Gemini 모델을 사용하여 오디오 파일에서 타임스탬프와 트랜스크립트 세그먼트를 정밀 추출합니다.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 필요합니다.")

    client = genai.Client(api_key=key)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    # 1. 파일 업로드
    print(f"[STT Service] 오디오 파일 업로드 중: {audio_path}")
    uploaded_file = client.files.upload(
        file=audio_path,
        config=types.UploadFileConfig(mime_type=mime_type) if mime_type else None,
    )

    while uploaded_file.state.name == "PROCESSING":
        print("[STT Service] 파일 처리 대기 중...")
        time.sleep(1)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise RuntimeError("Google GenAI 파일 처리에 실패했습니다.")

    try:
        # 2. 프롬프트 작성
        system_instruction = (
            "당신은 최고 수준의 음성 인식(STT) 및 자막 제작 전문가입니다. "
            "주어진 오디오를 듣고 한국어/영어에 맞춰 정확한 타임스탬프와 대화 내용을 출력하세요."
        )

        prompt = """
이 오디오를 분석하여 다음 형식에 맞춰 한국어로 자세하고 정확하게 전사 및 요약을 작성해주세요.

### [1] 💡 핵심 요약
- **한 줄 요약**: 영상의 핵심 주제 요약
- **주요 내용**:
  - 핵심 포인트 3가지 불릿

### [2] ⏱️ 타임스탬프 및 화자별 대화 (Timestamped & Diarized Transcript)
- 각 발화마다 빠짐없이 정확한 시간대 [MM:SS]와 화자, 대사를 작성하세요.
- 반드시 아래 형식을 지켜주세요:
- [00:00] 화자 1: 대화 내용
- [00:05] 화자 2: 대화 내용
- [00:15] 가이: 대화 내용

### [3] 📝 전체 전문 (Full Transcript)
- 읽기 쉽게 정리된 전체 전사 텍스트를 작성하세요.
"""

        # 모델 호출 (gemini-3.7-flash / gemini-3.8-flash / gemini-3.6-flash / gemini-3.5-flash)
        target_models = [model_name, "gemini-3.7-flash", "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
        full_text = ""
        model_used = model_name
        last_err = None

        for m in target_models:
            try:
                print(f"[STT Service] {m} 모델로 전사 생성 시도 중...")
                response = client.models.generate_content(
                    model=m,
                    contents=[
                        uploaded_file,
                        types.Part.from_text(text=prompt),
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                if response.text:
                    full_text = response.text
                    model_used = m
                    break
            except Exception as e:
                print(f"[STT Service] {m} 실패: {e}")
                last_err = e
                continue

        if not full_text:
            raise RuntimeError(f"STT 전사 실패: {last_err}")

        # 3. 세그먼트 파싱
        segments = parse_transcript_segments(full_text)

        # 4. 섹션 파싱
        summary_text = ""
        full_transcript_text = full_text

        if "### [1] 💡 핵심 요약" in full_text:
            parts = full_text.split("### [1] 💡 핵심 요약")
            rest = parts[1] if len(parts) > 1 else ""
            if "### [2] ⏱️ 타임스탬프" in rest:
                p2 = rest.split("### [2] ⏱️ 타임스탬프")
                summary_text = p2[0].strip()
                rest2 = p2[1]
                if "### [3] 📝 전체 전문" in rest2:
                    p3 = rest2.split("### [3] 📝 전체 전문")
                    full_transcript_text = p3[1].strip()

        return {
            "model_used": model_used,
            "full_content": full_text,
            "summary": summary_text,
            "segments": segments,
            "full_transcript": full_transcript_text,
        }

    finally:
        try:
            client.files.delete(name=uploaded_file.name)
            print(f"[STT Service] 원격 임시 파일 삭제 완료: {uploaded_file.name}")
        except Exception as e:
            print(f"[STT Service] 파일 삭제 중 알림: {e}")

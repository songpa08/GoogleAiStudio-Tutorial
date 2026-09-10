import os
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types


def answer_video_question(
    question: str,
    video_title: str,
    transcript_text: str,
    segments: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.8-flash",
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Gemini 3.8 Flash 모델을 사용하여 전사된 영상 트랜스크립트 컨텍스트를 기반으로 사용자 질문에 답변합니다.
    답변 내에 [MM:SS] 형식의 타임스탬프를 적극적으로 인용하도록 유도합니다.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY가 필요합니다.")

    client = genai.Client(api_key=key)

    system_instruction = f"""
당신은 YouTube 영상의 내용을 완벽하게 파악하고 있는 똑똑한 AI 비디오 어시스턴트입니다.
현재 사용자가 보고 있는 영상의 제목은 다음과 같습니다:
《{video_title}》

아래는 해당 영상의 전체 대화 및 타임스탬프 트랜스크립트입니다:
==================================================
{transcript_text}
==================================================

[답변 원칙]:
1. 사용자의 질문에 친절하고 명확하게 한국어로 답변하세요.
2. 답변할 때 근거가 되는 영상의 시간대(타임스탬프)를 반드시 [MM:SS] 또는 [HH:MM:SS] 형식으로 포함하세요.
   (예: "상진님이 이야기한 부분은 [00:15]에서 확인할 수 있습니다.")
3. 사용자가 특정 내용의 위치나 시점을 물어보면, 가장 관련성이 높은 시간대를 정확히 짚어주세요.
4. 트랜스크립트에 없는 내용은 상상해서 답하지 말고, 영상에 언급되지 않았다고 정직하게 밝히세요.
"""

    prompt = f"사용자 질문: {question}"

    # 모델 호출 (gemini-3.8-flash 사용, 미지원 시 fallback)
    target_models = [model_name, "gemini-3.7-flash", "gemini-3.6-flash"]
    last_err = None

    for model in target_models:
        try:
            print(f"[QA Service] {model} 모델로 질문 답변 생성 중...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            return {
                "answer": response.text or "답변을 생성하지 못했습니다.",
                "model_used": model,
                "question": question,
            }
        except Exception as e:
            print(f"[QA Service] {model} 호출 실패: {e}")
            last_err = e
            continue

    raise RuntimeError(f"AI Q&A 생성에 실패했습니다: {last_err}")

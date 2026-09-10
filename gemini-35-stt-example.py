# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
import sys
from google import genai
from google.genai import types


def generate(audio_path="output.wav"):
    if not os.path.exists(audio_path):
        print(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        return

    print(f"'{audio_path}' 오디오 파일을 읽는 중...")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3.5-transcribe"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav",
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        ),
    )

    print("음성 전사(STT) 진행 중...\n")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")
    print()

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "output.wav"
    generate(audio_file)



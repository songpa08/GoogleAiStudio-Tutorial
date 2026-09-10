# To run this code you need to install the following dependencies:
# pip install google-genai lameenc

import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3.1-flash-tts-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""## Scene:
Scene:
  Location: State-of-the-art live TV newsroom studio
  Acoustics: Dry, pristine studio recording with minimal room reverb and tight broadcast proximity
  Atmosphere: Urgent, high-stakes breaking news environment with on-air tension
  Visual Cue: News anchor sitting at the main desk under studio lights, reading the teleprompter with breaking graphics flashing on screen

## Sample Context:
Context:
  Speaker:
    Name: News Anchor
    Persona: Veteran prime-time tech news journalist
    Base Tone: Authoritative, articulate, credible, yet genuinely amazed
    Pacing: Fast and rhythmic during headlines, deliberate and slowed down for dramatic emphasis
  Directives:
    - Deliver the opening sentence with high energy and an urgent breaking news cadence.
    - Insert a brief suspenseful pause right before revealing the pricing details.
    - Use a conspiratorial whisper when bringing up the industry secret/price shock.
    - Let out a spontaneous gasp of disbelief followed by a slight chuckle at the absurdly cheap price.
    - Conclude with a strong, professional broadcast sign-off.

## Transcript:
[excited] 뉴스 특보입니다! 전 세계 테크 업계를 완전히 뒤흔들 충격적인 소식이 방금 전 전해졌습니다.

구글이 차세대 플래그십 AI 모델, [pause] '제미나이 4.0 Pro'를 전격 출시했습니다!

인간의 추론 능력을 뛰어넘는 벤치마크 점수와 실시간 멀티모달 기능도 압도적이지만, [whispers] 오늘 전 세계 엔지니어들을 경악하게 만든 진짜 이유는 따로 있습니다. 바로 믿기 힘든 '가격표'입니다.

[gasp] 100만 토큰당 이용료가... [pause] 무려 단돈 10원입니다! [laughs] 

네, 방송 사고나 전산 오류가 아닙니다! 기존 상용 모델 대비 100분의 1도 안 되는 파격적인 가격 책정에, 실리콘밸리 경쟁사들은 지금 그야말로 패닉 상태에 빠졌습니다.

[excited] AI 기술의 진입 장벽을 완전히 허물어버린 구글의 파격적인 승부수! [pause] 자세한 시장 반응과 후속 소식은 잠시 후 종합뉴스에서 집중 보도해 드리겠습니다. 지금까지 뉴스 특보였습니다."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Zephyr"
                )
            )
        ),
    )

    audio_data_chunks = []
    audio_mime_type = "audio/L16;rate=24000"

    print("오디오 생성 중...")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.parts is None:
            continue
        for part in chunk.parts:
            if part.inline_data and part.inline_data.data:
                audio_data_chunks.append(part.inline_data.data)
                if part.inline_data.mime_type:
                    audio_mime_type = part.inline_data.mime_type
            elif part.text:
                print(part.text, end="")

    if audio_data_chunks:
        combined_audio = b"".join(audio_data_chunks)
        parameters = parse_audio_mime_type(audio_mime_type)
        sample_rate = parameters.get("rate") or 24000

        # MP3로 압축 저장 (약 500KB로 용량 대폭 감소, 고음질 유지)
        output_mp3 = "output.mp3"
        saved_mp3 = save_as_mp3(combined_audio, sample_rate, output_mp3, bitrate_kbps=64)

        # WAV 파일로도 저장
        output_wav = "output.wav"
        wav_data = convert_to_wav(combined_audio, audio_mime_type)
        save_binary_file(output_wav, wav_data)

        if saved_mp3:
            mp3_size_kb = os.path.getsize(output_mp3) / 1024
            print(f"\n[MP3 압축 완료 (약 500KB)] : {output_mp3} ({mp3_size_kb:.1f} KB)")
        wav_size_mb = os.path.getsize(output_wav) / (1024 * 1024)
        print(f"[원본 WAV 저장 완료]       : {output_wav} ({wav_size_mb:.2f} MB)")
    else:
        print("\n생성된 오디오 데이터가 없습니다.")


def save_as_mp3(pcm_data: bytes, sample_rate: int, output_file: str, bitrate_kbps: int = 64) -> bool:
    """PCM 오디오 데이터를 지정된 비트레이트의 MP3 파일로 압축 저장합니다."""
    try:
        import lameenc
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(bitrate_kbps)
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(1)
        encoder.set_quality(2)

        mp3_data = encoder.encode(pcm_data)
        mp3_data += encoder.flush()

        save_binary_file(output_file, mp3_data)
        return True
    except ImportError:
        print("MP3 인코딩을 위해 'pip install lameenc' 가 필요합니다.")
        return False

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    generate()

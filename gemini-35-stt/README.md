# Gemini 3.5 Transcribe STT (Speech-to-Text) 코드 설명서

이 문서는 `gemini-35-stt-example.py` 코드의 각 라인이 어떤 역할을 하는지 줄 단위(Line-by-Line)로 상세히 설명합니다.

---

## 📌 개요

Google의 `gemini-3.5-transcribe` 모델을 사용하여 로컬 오디오 파일(`.wav`)을 입력받아 텍스트로 음성 전사(Speech-to-Text)를 수행하는 예제 코드입니다.

- **지원 모델**: `gemini-3.5-transcribe`
- **주요 기능**:
  - 로컬 `.wav` 바이너리 데이터를 직접 모델 입력(`Part.from_bytes`)으로 전달
  - 단어별 타임스탬프(`word_timestamp=True`) 및 화자 분리(`diarization=True`) 기능 활성화
  - 실시간 스트리밍 출력(`generate_content_stream`)

---

## 🛠️ 사전 준비 사항 (Dependencies)

```bash
pip install google-genai
```

환경 변수로 Gemini API 키가 설정되어 있어야 합니다:
```bash
export GEMINI_API_KEY="your_api_key_here"  # Linux / macOS
set GEMINI_API_KEY="your_api_key_here"     # Windows CMD
$env:GEMINI_API_KEY="your_api_key_here"    # Windows PowerShell
```

---

## 🔍 Line-by-Line 코드 상세 설명

### 1. 의존성 및 모듈 임포트 (Lines 1 ~ 8)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
3: 
4: import base64
5: import os
6: import sys
7: from google import genai
8: from google.genai import types
```

- **Line 1~2**: 코드 실행에 필요한 패키지(`google-genai`) 설치 안내 주석입니다.
- **Line 4**: `base64` - 바이너리 데이터 인코딩/디코딩 모듈입니다.
- **Line 5**: `os` - 파일 존재 여부 확인(`os.path.exists`) 및 환경 변수 조회(`os.environ.get`)를 위한 표준 라이브러리입니다.
- **Line 6**: `sys` - CLI 명령행 인수(`sys.argv`)를 통해 처리할 오디오 파일 경로를 전달받기 위한 모듈입니다.
- **Line 7~8**: `from google import genai`, `from google.genai import types` - Google GenAI SDK 클라이언트와 파라미터 설정을 위한 타입들을 불러옵니다.

---

### 2. 음성 파일 로드 및 검증 (Lines 11 ~ 18)

```python
11: def generate(audio_path="output.wav"):
12:     if not os.path.exists(audio_path):
13:         print(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
14:         return
15: 
16:     print(f"'{audio_path}' 오디오 파일을 읽는 중...")
17:     with open(audio_path, "rb") as f:
18:         audio_bytes = f.read()
```

- **Line 11**: `generate` 함수를 정의하며, 인자가 없을 경우 기본값으로 `"output.wav"`를 사용합니다.
- **Line 12~14**: `os.path.exists(audio_path)`를 통해 지정된 파일이 실제로 존재하는지 검사하고, 없으면 에러 메시지를 출력 후 안전하게 종료합니다.
- **Line 16**: 오디오 파일 로딩 시작 메시지를 출력합니다.
- **Line 17~18**: `open(..., "rb")`로 오디오 파일을 바이너리 읽기 모드로 열어 전체 바이트 데이터(`audio_bytes`)를 메모리에 로드합니다.

---

### 3. 클라이언트 초기화 및 입력 페이로드 구성 (Lines 20 ~ 35)

```python
20:     client = genai.Client(
21:         api_key=os.environ.get("GEMINI_API_KEY"),
22:     )
23: 
24:     model = "gemini-3.5-transcribe"
25:     contents = [
26:         types.Content(
27:             role="user",
28:             parts=[
29:                 types.Part.from_bytes(
30:                     data=audio_bytes,
31:                     mime_type="audio/wav",
32:                 ),
33:             ],
34:         ),
35:     ]
```

- **Line 20~22**: 환경 변수에 등록된 `GEMINI_API_KEY`를 사용하여 GenAI 클라이언트를 생성합니다.
- **Line 24**: STT 전용 모델인 `"gemini-3.5-transcribe"`를 지정합니다.
- **Line 25~28**: 모델 요청 객체 `contents`를 사용자(`role="user"`) 역할로 구성합니다.
- **Line 29~32**: `types.Part.from_bytes()`를 사용하여 읽어들인 오디오 바이트(`data=audio_bytes`)와 MIME 타입(`mime_type="audio/wav"`)을 모델 입력 파트로 설정합니다.

---

### 4. STT 옵션 설정 (Lines 36 ~ 41)

```python
36:     generate_content_config = types.GenerateContentConfig(
37:         audio_transcription_config=types.AudioTranscriptionConfig(
38:             word_timestamp=True,
39:             diarization=True,
40:         ),
41:     )
```

- **Line 36**: `GenerateContentConfig`를 생성하여 전사 관련 추가 옵션을 지정합니다.
- **Line 37**: `audio_transcription_config`에 세부 STT 옵션을 전달합니다.
- **Line 38**: `word_timestamp=True` - 전사된 각 단어의 시작 및 종료 시간(타임스탬프) 정보를 제공하도록 활성화합니다.
- **Line 39**: `diarization=True` - 오디오에 등장하는 화자를 분리하여 구분(화자 분리)하도록 설정합니다.

---

### 5. 스트리밍 음성 전사 실행 및 출력 (Lines 43 ~ 51)

```python
43:     print("음성 전사(STT) 진행 중...\n")
44:     for chunk in client.models.generate_content_stream(
45:         model=model,
46:         contents=contents,
47:         config=generate_content_config,
48:     ):
49:         if text := chunk.text:
50:             print(text, end="")
51:     print()
```

- **Line 43**: 전사 시작을 알리는 로그를 출력합니다.
- **Line 44~48**: `generate_content_stream`을 호출하여 전사 결과를 실시간 청크 단위로 스트리밍 수신합니다.
- **Line 49~50**: `if text := chunk.text:` (월러스 연산자)로 청크에 텍스트가 존재하는 경우 개행 없이 이어서 콘솔에 출력합니다.
- **Line 51**: 스트리밍이 완료된 후 마지막에 줄바꿈을 수행합니다.

---

### 6. 실행 진입점 및 명령행 인수 처리 (Lines 53 ~ 55)

```python
53: if __name__ == "__main__":
54:     audio_file = sys.argv[1] if len(sys.argv) > 1 else "output.wav"
55:     generate(audio_file)
```

- **Line 53**: 직접 실행 여부를 판단하는 파이썬 관용구입니다.
- **Line 54**: 실행 시 터미널에서 인자(예: `python gemini-35-stt-example.py my_voice.wav`)를 넘겼으면 해당 파일명을, 없으면 기본값 `"output.wav"`를 선택합니다.
- **Line 55**: 결정된 오디오 파일 경로로 `generate()` 함수를 실행합니다.

---

## 🚀 실행 방법

### 기본 파일(`output.wav`) 전사:
```bash
python gemini-35-stt-example.py
```

### 다른 오디오 파일 지정하여 전사:
```bash
python gemini-35-stt-example.py custom_audio.wav
```

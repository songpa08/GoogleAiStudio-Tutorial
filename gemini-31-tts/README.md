# Gemini 3.1 Flash TTS (Text-to-Speech) 코드 설명서

이 문서는 `gemini-31-tts-example.py` 코드의 각 라인이 어떤 역할을 하는지 줄 단위(Line-by-Line)로 상세히 설명합니다.

---

## 📌 개요

Google의 `gemini-3.1-flash-tts-preview` 모델을 사용하여 자연스러운 음성을 생성하고, 수신된 PCM 오디오 스트림 데이터를 **MP3** 및 **WAV** 파일로 저장하는 예제 코드입니다.

- **지원 모델**: `gemini-3.1-flash-tts-preview`
- **주요 기능**: 감정/분위기/화자 지시문(Directives)을 반영한 음성 생성, 오디오 스트리밍 처리, MP3 압축 인코딩, WAV 헤더 패킹

---

## 🛠️ 사전 준비 사항 (Dependencies)

```bash
pip install google-genai lameenc
```

- `google-genai`: Google Gen AI 공식 Python SDK
- `lameenc`: PCM 원시 데이터를 고음질/저용량 MP3로 변환하기 위한 C 기반 LAME 인코더 바인딩

환경 변수로 Gemini API 키가 설정되어 있어야 합니다:
```bash
export GEMINI_API_KEY="your_api_key_here"  # Linux / macOS
set GEMINI_API_KEY="your_api_key_here"     # Windows CMD
$env:GEMINI_API_KEY="your_api_key_here"    # Windows PowerShell
```

---

## 🔍 Line-by-Line 코드 상세 설명

### 1. 의존성 및 모듈 임포트 (Lines 1 ~ 9)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai lameenc
3: 
4: import mimetypes
5: import os
6: import re
7: import struct
8: from google import genai
9: from google.genai import types
```

- **Line 1~2**: 코드 실행에 필요한 패키지(`google-genai`, `lameenc`) 설치 안내 주석입니다.
- **Line 4**: `mimetypes` - MIME 타입 처리를 위한 파이썬 표준 라이브러리입니다.
- **Line 5**: `os` - 환경 변수 조회(`os.environ.get`) 및 파일 크기 확인(`os.path.getsize`)을 위한 운영체제 인터페이스 모듈입니다.
- **Line 6**: `re` - 정규 표현식 모듈입니다.
- **Line 7**: `struct` - 파이썬 값과 C 구조체 바이너리 데이터를 상호 변환하는 모듈로, 순수 PCM 데이터에 WAV 헤더를 직접 작성(패킹)할 때 사용됩니다.
- **Line 8~9**: `from google import genai`, `from google.genai import types` - 신규 Google GenAI SDK 클라이언트와 설정/파라미터 타입들을 불러옵니다.

---

### 2. 바이너리 파일 저장 함수 (Lines 12 ~ 16)

```python
12: def save_binary_file(file_name, data):
13:     f = open(file_name, "wb")
14:     f.write(data)
15:     f.close()
16:     print(f"File saved to to: {file_name}")
```

- **Line 12**: 파일명과 바이너리 데이터를 받아 디스크에 저장하는 헬퍼 함수 정의입니다.
- **Line 13**: `"wb"` (바이너리 쓰기 모드)로 파일을 엽니다.
- **Line 14**: 전달받은 바이트 데이터(`data`)를 파일에 기록합니다.
- **Line 15**: 파일 핸들을 닫아 저장 작업을 완료합니다.
- **Line 16**: 저장 완료 메시지와 경로를 콘솔에 출력합니다.

---

### 3. 메인 TTS 생성 함수 - 클라이언트 및 프롬프트 정의 (Lines 19 ~ 64)

```python
19: def generate():
20:     client = genai.Client(
21:         api_key=os.environ.get("GEMINI_API_KEY"),
22:     )
23: 
24:     model = "gemini-3.1-flash-tts-preview"
25:     contents = [
26:         types.Content(
27:             role="user",
28:             parts=[
29:                 types.Part.from_text(text="""## Scene:
30: Scene:
31:   Location: State-of-the-art live TV newsroom studio
32:   Acoustics: Dry, pristine studio recording with minimal room reverb and tight broadcast proximity
33:   Atmosphere: Urgent, high-stakes breaking news environment with on-air tension
34:   Visual Cue: News anchor sitting at the main desk under studio lights, reading the teleprompter with breaking graphics flashing on screen
35: 
36: ## Sample Context:
37: Context:
38:   Speaker:
39:     Name: News Anchor
40:     Persona: Veteran prime-time tech news journalist
41:     Base Tone: Authoritative, articulate, credible, yet genuinely amazed
42:     Pacing: Fast and rhythmic during headlines, deliberate and slowed down for dramatic emphasis
43:   Directives:
44:     - Deliver the opening sentence with high energy and an urgent breaking news cadence.
45:     - Insert a brief suspenseful pause right before revealing the pricing details.
46:     - Use a conspiratorial whisper when bringing up the industry secret/price shock.
47:     - Let out a spontaneous gasp of disbelief followed by a slight chuckle at the absurdly cheap price.
48:     - Conclude with a strong, professional broadcast sign-off.
49: 
50: ## Transcript:
51: [excited] 뉴스 특보입니다! 전 세계 테크 업계를 완전히 뒤흔들 충격적인 소식이 방금 전 전해졌습니다.
...
61: [excited] AI 기술의 진입 장벽을 완전히 허물어버린 구글의 파격적인 승부수! [pause] 자세한 시장 반응과 후속 소식은 잠시 후 종합뉴스에서 집중 보도해 드리겠습니다. 지금까지 뉴스 특보였습니다."""),
62:             ],
63:         ),
64:     ]
```

- **Line 20~22**: 환경 변수 `GEMINI_API_KEY`에서 API 키를 읽어와 `genai.Client` 인스턴스를 초기화합니다.
- **Line 24**: 사용할 모델명을 `"gemini-3.1-flash-tts-preview"`로 지정합니다.
- **Line 25~28**: 모델에 전달할 `contents` 객체를 구성합니다.
- **Line 29~35 (`## Scene`)**: 장면의 장소(생방송 뉴스룸), 음향 환경(울림 없는 스튜디오 녹음), 분위기를 지정하여 음향 질감을 제어합니다.
- **Line 36~48 (`## Sample Context & Directives`)**: 화자 페르소나(베테랑 뉴스 앵커), 목소리 톤(권위 있고 놀란 어조), 템포 및 구체적인 연기 지시사항(속삭임, 탄식, 웃음, 일시정지)을 명시합니다.
- **Line 50~61 (`## Transcript`)**: 실제로 발화될 대본이며, `[excited]`, `[pause]`, `[whispers]`, `[gasp]`, `[laughs]` 등의 연출 태그를 포함하여 모델이 감정을 표현하도록 유도합니다.

---

### 4. TTS 설정 구성 (Lines 65 ~ 77)

```python
65:     generate_content_config = types.GenerateContentConfig(
66:         temperature=1,
67:         response_modalities=[
68:             "audio",
69:         ],
70:         speech_config=types.SpeechConfig(
71:             voice_config=types.VoiceConfig(
72:                 prebuilt_voice_config=types.PrebuiltVoiceConfig(
73:                     voice_name="Zephyr"
74:                 )
75:             )
76:         ),
77:     )
```

- **Line 65**: 생성 설정을 위한 `GenerateContentConfig` 객체를 생성합니다.
- **Line 66**: `temperature=1`로 설정하여 음성 톤의 자연스러운 뉘앙스와 감정 표현을 살립니다.
- **Line 67~69**: `response_modalities=["audio"]`를 통해 텍스트 대신 **오디오**를 응답으로 수신하도록 지정합니다.
- **Line 70~76**: `speech_config`에서 내장 음성(Prebuilt Voice)을 선택합니다. 여기서는 `"Zephyr"` 보이스를 적용했습니다. (다른 음성: `Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede` 등 사용 가능)

---

### 5. 오디오 스트림 수신 및 청크 병합 (Lines 79 ~ 97)

```python
79:     audio_data_chunks = []
80:     audio_mime_type = "audio/L16;rate=24000"
81: 
82:     print("오디오 생성 중...")
83:     for chunk in client.models.generate_content_stream(
84:         model=model,
85:         contents=contents,
86:         config=generate_content_config,
87:     ):
88:         if chunk.parts is None:
89:             continue
90:         for part in chunk.parts:
91:             if part.inline_data and part.inline_data.data:
92:                 audio_data_chunks.append(part.inline_data.data)
93:                 if part.inline_data.mime_type:
94:                     audio_mime_type = part.inline_data.mime_type
95:             elif part.text:
96:                 print(part.text, end="")
```

- **Line 79**: 스트리밍으로 전달되는 오디오 바이너리 조각들을 모으기 위한 리스트 `audio_data_chunks`를 선언합니다.
- **Line 80**: 기본 오디오 MIME 타입(`audio/L16;rate=24000`, 16-bit PCM 24kHz)을 초기값으로 둡니다.
- **Line 83~87**: `client.models.generate_content_stream(...)`을 호출하여 오디오 청크를 실시간 스트림으로 수신합니다.
- **Line 88~89**: 응답 청크의 `parts`가 비어있으면 건너뜁니다.
- **Line 90~94**: 각 파트에서 `inline_data`가 있으면 오디오 바이트(`data`)를 리스트에 추가하고, 전달된 MIME 타입을 갱신합니다.
- **Line 95~96**: 혹시 모델이 텍스트 출력을 반환할 경우 콘솔에 즉시 출력합니다.

---

### 6. 오디오 파일 변환 및 저장 (Lines 99 ~ 119)

```python
99:     if audio_data_chunks:
100:         combined_audio = b"".join(audio_data_chunks)
101:         parameters = parse_audio_mime_type(audio_mime_type)
102:         sample_rate = parameters.get("rate") or 24000
103: 
104:         # MP3로 압축 저장 (약 500KB로 용량 대폭 감소, 고음질 유지)
105:         output_mp3 = "output.mp3"
106:         saved_mp3 = save_as_mp3(combined_audio, sample_rate, output_mp3, bitrate_kbps=64)
107: 
108:         # WAV 파일로도 저장
109:         output_wav = "output.wav"
110:         wav_data = convert_to_wav(combined_audio, audio_mime_type)
111:         save_binary_file(output_wav, wav_data)
112: 
113:         if saved_mp3:
114:             mp3_size_kb = os.path.getsize(output_mp3) / 1024
115:             print(f"\n[MP3 압축 완료 (약 500KB)] : {output_mp3} ({mp3_size_kb:.1f} KB)")
116:         wav_size_mb = os.path.getsize(output_wav) / (1024 * 1024)
117:         print(f"[원본 WAV 저장 완료]       : {output_wav} ({wav_size_mb:.2f} MB)")
118:     else:
119:         print("\n생성된 오디오 데이터가 없습니다.")
```

- **Line 99~100**: 수신된 모든 오디오 청크를 하나로 합칩니다 (`b"".join`).
- **Line 101~102**: MIME 문자열에서 샘플 레이트(기본 24,000Hz)를 파싱합니다.
- **Line 104~106**: `save_as_mp3` 함수를 호출하여 순수 PCM 데이터를 64kbps MP3 파일(`output.mp3`)로 인코딩하여 저장합니다.
- **Line 108~111**: `convert_to_wav` 함수를 통해 표준 RIFF/WAV 헤더를 붙인 뒤 `output.wav`로 저장합니다.
- **Line 113~117**: 저장된 MP3 및 WAV 파일의 실제 용량을 계산하여 콘솔에 안내합니다.

---

### 7. MP3 인코딩 함수 (Lines 121 ~ 138)

```python
121: def save_as_mp3(pcm_data: bytes, sample_rate: int, output_file: str, bitrate_kbps: int = 64) -> bool:
122:     """PCM 오디오 데이터를 지정된 비트레이트의 MP3 파일로 압축 저장합니다."""
123:     try:
124:         import lameenc
125:         encoder = lameenc.Encoder()
126:         encoder.set_bit_rate(bitrate_kbps)
127:         encoder.set_in_sample_rate(sample_rate)
128:         encoder.set_channels(1)
129:         encoder.set_quality(2)
130: 
131:         mp3_data = encoder.encode(pcm_data)
132:         mp3_data += encoder.flush()
133: 
134:         save_binary_file(output_file, mp3_data)
135:         return True
136:     except ImportError:
137:         print("MP3 인코딩을 위해 'pip install lameenc' 가 필요합니다.")
138:         return False
```

- **Line 124~125**: `lameenc` 라이브러리를 동적으로 가져와 `Encoder` 객체를 생성합니다.
- **Line 126~129**: 비트레이트(64kbps), 입력 샘플 레이트(24,000Hz), 채널 수(1 = 모노), 인코딩 품질(2 = 고품질)을 설정합니다.
- **Line 131~132**: PCM 데이터를 MP3 바이트 스트림으로 변환하고, 잔여 버퍼를 `flush()`하여 바이트를 완성합니다.
- **Line 134~135**: 완성된 바이트 데이터를 파일로 저장하고 성공(`True`)을 반환합니다.
- **Line 136~138**: `lameenc`가 설치되지 않은 경우 예외 처리 및 안내 메시지를 출력합니다.

---

### 8. WAV 헤더 생성 및 바이너리 패킹 함수 (Lines 140 ~ 179)

```python
140: def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
...
150:     parameters = parse_audio_mime_type(mime_type)
151:     bits_per_sample = parameters["bits_per_sample"]
152:     sample_rate = parameters["rate"]
153:     num_channels = 1
154:     data_size = len(audio_data)
155:     bytes_per_sample = bits_per_sample // 8
156:     block_align = num_channels * bytes_per_sample
157:     byte_rate = sample_rate * block_align
158:     chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size
159: 
160:     # http://soundfile.sapp.org/doc/WaveFormat/
161: 
162:     header = struct.pack(
163:         "<4sI4s4sIHHIIHH4sI",
164:         b"RIFF",          # ChunkID
165:         chunk_size,       # ChunkSize (total file size - 8 bytes)
166:         b"WAVE",          # Format
167:         b"fmt ",          # Subchunk1ID
168:         16,               # Subchunk1Size (16 for PCM)
169:         1,                # AudioFormat (1 for PCM)
170:         num_channels,     # NumChannels
171:         sample_rate,      # SampleRate
172:         byte_rate,        # ByteRate
173:         block_align,      # BlockAlign
174:         bits_per_sample,  # BitsPerSample
175:         b"data",          # Subchunk2ID
176:         data_size         # Subchunk2Size (size of audio data)
177:     )
178:     return header + audio_data
```

- **Line 150~158**: 오디오 파라미터(16-bit, 24kHz, 1채널)를 기준으로 헤더 규격에 필요한 값들(`block_align`, `byte_rate`, `chunk_size`)을 계산합니다.
- **Line 162~177**: `struct.pack("<4sI4s4sIHHIIHH4sI", ...)`를 사용해 리틀 엔디언(`<`) 포맷으로 44바이트 표준 RIFF WAV 헤더를 생성합니다.
- **Line 178**: 44바이트 헤더 뒤에 원시 PCM 데이터를 연결(`header + audio_data`)하여 온전한 WAV 바이너리를 반환합니다.

---

### 9. MIME 타입 파싱 함수 및 실행 진입점 (Lines 180 ~ 218)

```python
180: def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
...
192:     bits_per_sample = 16
193:     rate = 24000
194: 
195:     parts = mime_type.split(";")
196:     for param in parts:
...
209:             try:
210:                 bits_per_sample = int(param.split("L", 1)[1])
...
212:     return {"bits_per_sample": bits_per_sample, "rate": rate}
215: if __name__ == "__main__":
216:     generate()
```

- **Line 180~212**: `"audio/L16;rate=24000"` 같은 MIME 문자열을 파싱하여 비트 수(`bits_per_sample: 16`)와 샘플 레이트(`rate: 24000`)를 딕셔너리로 추출합니다.
- **Line 215~216**: 파이썬 스크립트가 직접 실행될 때 `generate()` 함수를 호출하는 메인 진입점입니다.

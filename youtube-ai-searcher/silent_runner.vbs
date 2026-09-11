' AI YouTube Searcher 백그라운드 무음(Silent) 자동 실행기
Set WshShell = CreateObject("WScript.Shell")

Dim projectDir, pythonExec, command
projectDir = "C:\Users\yunjo\Desktop\AI Agent\projet\GoogleAiStudio-Tutorial\youtube-ai-searcher"
pythonExec = "C:\Users\yunjo\miniconda3\envs\myenv\python.exe"

' 작업 디렉터리 설정
WshShell.CurrentDirectory = projectDir

' uvicorn 서버를 백그라운드 창 숨김(0) 모드로 비동기 실행
command = """" & pythonExec & """ -m uvicorn app:app --host 0.0.0.0 --port 8001"
WshShell.Run command, 0, False

@echo off
chcp 65001 > nul
echo ===================================================
echo   AI YouTube Searcher 웹서버를 시작합니다...
echo ===================================================
echo.

set PYTHON_EXEC=C:\Users\yunjo\miniconda3\envs\myenv\python.exe

if not exist "%PYTHON_EXEC%" (
    echo [경고] myenv 파이썬 경로를 찾을 수 없어 시스템 기본 python을 사용합니다.
    set PYTHON_EXEC=python
)

cd /d "%~dp0"
echo 접속 주소: http://localhost:8001
echo 서버를 종료하려면 이 창에서 Ctrl + C를 누르세요.
echo.

"%PYTHON_EXEC%" -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

pause

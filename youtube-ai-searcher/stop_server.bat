@echo off
chcp 65001 > nul
echo ========================================================
echo   AI YouTube Searcher - 실행 중인 웹서버 종료
echo ========================================================
echo.

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001 ^| findstr LISTENING') do (
    echo [종료 중] 포트 8001 프로세스 (PID: %%a) 종료...
    taskkill /F /PID %%a > nul 2>&1
)

echo [완료] 서버가 정상적으로 종료되었습니다.
echo.
pause

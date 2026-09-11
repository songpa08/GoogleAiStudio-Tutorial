@echo off
chcp 65001 > nul
echo ========================================================
echo   AI YouTube Searcher - Windows 자동 시작 등록 해제
echo ========================================================
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set TARGET_VBS=%STARTUP_DIR%\AI_YouTube_Searcher.vbs

if exist "%TARGET_VBS%" (
    del "%TARGET_VBS%"
    echo [완료] Windows 자동 시작 등록이 성공적으로 해제되었습니다.
) else (
    echo [안내] 자동 시작으로 등록되어 있지 않습니다.
)

echo.
pause

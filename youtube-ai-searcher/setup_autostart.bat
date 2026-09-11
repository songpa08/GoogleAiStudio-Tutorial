@echo off
chcp 65001 > nul
echo ========================================================
echo   AI YouTube Searcher - Windows 자동 시작 등록
echo ========================================================
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set TARGET_VBS=%STARTUP_DIR%\AI_YouTube_Searcher.vbs
set RUNNER_VBS=%~dp0silent_runner.vbs

echo Set WshShell = CreateObject("WScript.Shell") > "%TARGET_VBS%"
echo WshShell.Run "wscript.exe """ ^& "%RUNNER_VBS%" ^& """", 0, False >> "%TARGET_VBS%"

echo [성공] Windows 시작 시 자동으로 백그라운드 구동되도록 등록되었습니다!
echo 등록 위치: %TARGET_VBS%
echo.
pause

@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Mindily - Share on Wi-Fi
set PORT=8020

echo ============================================================
echo   Mindily : share with phones on the SAME Wi-Fi
echo ============================================================
echo.

taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do taskkill /F /PID %%P >nul 2>&1
timeout /t 2 /nobreak >nul

if not exist .venv\Scripts\python.exe (
  echo Run SETUP_AND_SHARE.cmd once first.
  pause
  exit /b 1
)
set "PY=.venv\Scripts\python.exe"

echo Finding this computer's Wi-Fi address...
set "IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /C:"IPv4"') do (
  for /f "tokens=* delims= " %%B in ("%%A") do (
    echo %%B | findstr /B "192.168. 172. 10." >nul && if not defined IP set "IP=%%B"
  )
)

if not defined IP (
  echo Could not detect a Wi-Fi address. Run: ipconfig
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   Give testers this address ^(same Wi-Fi only^):
echo.
echo        http://!IP!:%PORT%
echo.
echo   Windows may ask to allow network access - click ALLOW.
echo   Keep this window open during the test.
echo ============================================================
echo.
"%PY%" -m uvicorn server:app --host 0.0.0.0 --port %PORT% --no-access-log
pause

@echo off
setlocal
cd /d "%~dp0"
title Mindily - Setup and Share
set PORT=8020

echo ============================================================
echo   Mindily : start server and make a public URL
echo   Keep BOTH windows open while testing.
echo ============================================================
echo.

REM ---------- 0. clean up leftovers from a previous run ----------
echo [0/4] Closing any leftover server or tunnel...
taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do taskkill /F /PID %%P >nul 2>&1
timeout /t 2 /nobreak >nul

REM ---------- 1. virtual environment ----------
if not exist .venv\Scripts\python.exe (
  echo [1/4] Creating virtual environment...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if not exist .venv\Scripts\python.exe (
    echo   FAILED: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
  )
)
set "PY=.venv\Scripts\python.exe"
echo [1/4] Virtual environment ready.

REM ---------- 2. dependencies ----------
echo [2/4] Checking dependencies...
"%PY%" -c "import torch, transformers, fastapi, uvicorn, httpx" 2>nul
if errorlevel 1 (
  echo    Installing ^(slow the first time^)...
  "%PY%" -m pip install --quiet --upgrade pip
  "%PY%" -m pip install --quiet -r requirements.txt
  if errorlevel 1 (
    echo   FAILED: could not install packages.
    pause
    exit /b 1
  )
)
echo [2/4] Dependencies ready.

REM ---------- 3. cloudflared ----------
if not exist .local-tools\cloudflared.exe (
  echo [3/4] Downloading cloudflared...
  if not exist .local-tools mkdir .local-tools
  powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile '.local-tools\cloudflared.exe'"
)
if not exist .local-tools\cloudflared.exe (
  echo   FAILED: cloudflared download blocked. See docs\QUICK_TUNNEL.md
  pause
  exit /b 1
)
echo [3/4] cloudflared ready.

REM ---------- 4. start server, then tunnel ----------
echo [4/4] Starting server on port %PORT%...
start "Mindily Server - KEEP OPEN" cmd /k ""%PY%" -m uvicorn server:app --host 127.0.0.1 --port %PORT% --no-access-log"

echo.
echo Waiting for the model to load...
set /a TRIES=0
:WAIT
timeout /t 10 /nobreak > nul
set /a TRIES+=1
powershell -NoProfile -Command "try { $r = Invoke-RestMethod 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 5; if ($r.status -eq 'ready') { exit 0 } else { exit 1 } } catch { exit 1 }"
if not errorlevel 1 goto READY
if %TRIES% GEQ 30 (
  echo   Server did not become ready. Check the server window.
  pause
  exit /b 1
)
echo   still loading... (%TRIES%)
goto WAIT

:READY
echo.
echo ============================================================
echo   Server READY. Opening the public tunnel.
echo   Copy the https://....trycloudflare.com address below.
echo   If it fails, run FIX_TUNNEL.cmd instead.
echo ============================================================
echo.
.local-tools\cloudflared.exe tunnel --protocol http2 --edge-ip-version 4 --url http://127.0.0.1:%PORT%
pause

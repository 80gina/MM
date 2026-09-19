@echo off
setlocal
cd /d "%~dp0"
title Mindily - Setup and Share

echo ============================================================
echo   Mindily : install, start server, make a public URL
echo   First run takes 10-20 min (PyTorch + model download).
echo   Keep BOTH windows open while testing.
echo ============================================================
echo.

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
echo [2/4] Installing dependencies (this is the slow part)...
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo   FAILED: could not install packages. Check your internet connection.
  pause
  exit /b 1
)
echo [2/4] Dependencies ready.

REM ---------- 3. cloudflared ----------
if not exist .local-tools\cloudflared.exe (
  echo [3/4] Downloading cloudflared...
  if not exist .local-tools mkdir .local-tools
  powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile '.local-tools\cloudflared.exe'"
  if not exist .local-tools\cloudflared.exe (
    echo   FAILED: download blocked. Get it manually, see docs\QUICK_TUNNEL.md
    pause
    exit /b 1
  )
)
echo [3/4] cloudflared ready.

REM ---------- 4. start server, then tunnel ----------
echo [4/4] Starting server on port 8010...
start "Mindily Server - KEEP OPEN" cmd /k ""%PY%" -m uvicorn server:app --host 127.0.0.1 --port 8010 --no-access-log"

echo.
echo Waiting for the model to load (first time: up to 5 minutes)...
set /a TRIES=0
:WAIT
timeout /t 10 /nobreak > nul
set /a TRIES+=1
powershell -NoProfile -Command "try { $r = Invoke-RestMethod 'http://127.0.0.1:8010/api/health' -TimeoutSec 5; if ($r.status -eq 'ready') { exit 0 } else { exit 1 } } catch { exit 1 }"
if not errorlevel 1 goto READY
if %TRIES% GEQ 40 (
  echo   Server did not become ready. Check the server window for errors.
  pause
  exit /b 1
)
echo   still loading... (%TRIES%)
goto WAIT

:READY
echo.
echo ============================================================
echo   Server is READY. Opening the public tunnel now.
echo   Copy the https://....trycloudflare.com address below
echo   and send it to your testers.
echo ============================================================
echo.
.local-tools\cloudflared.exe tunnel --url http://127.0.0.1:8010
pause

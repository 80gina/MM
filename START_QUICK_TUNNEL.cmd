@echo off
setlocal
cd /d "%~dp0"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"
if not exist ".local-tools\cloudflared.exe" (
  echo Cloudflare executable is missing. Follow docs\QUICK_TUNNEL.md first.
  pause
  exit /b 1
)
powershell -NoProfile -Command "try { $r = Invoke-RestMethod 'http://127.0.0.1:%PORT%/api/health' -TimeoutSec 5; if ($r.status -ne 'ready') { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo Mindily is not ready on port %PORT%. Start the Python server first.
  pause
  exit /b 1
)
echo Keep this window and the Python server open while users test.
echo Copy the https://...trycloudflare.com address shown below.
echo Press Ctrl+C to stop the tunnel.
".local-tools\cloudflared.exe" tunnel --url http://127.0.0.1:%PORT%
pause

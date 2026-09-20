@echo off
setlocal
cd /d "%~dp0"
title Mindily - Tunnel only
set PORT=8020
echo Trying alternative tunnel settings...
echo (The server window must already be running and READY.)
echo.
taskkill /F /IM cloudflared.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo --- attempt 1: http2 over IPv4 ---
.local-tools\cloudflared.exe tunnel --protocol http2 --edge-ip-version 4 --url http://127.0.0.1:%PORT%
echo.
echo If that failed, press a key to try QUIC.
pause >nul
.local-tools\cloudflared.exe tunnel --protocol quic --url http://127.0.0.1:%PORT%
pause

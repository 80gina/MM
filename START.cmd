@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Please follow README setup once before starting.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8000 after the server is ready.
.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000 --no-access-log
pause

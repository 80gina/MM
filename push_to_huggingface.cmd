@echo off
setlocal
cd /d "%~dp0_space_upload"

echo ==========================================================
echo   Hugging Face Space upload  -  yellowmug/mindily
echo ----------------------------------------------------------
echo   You will be asked to paste a WRITE token.
echo   Make one here (type: Write, not Read):
echo     https://huggingface.co/settings/tokens
echo   Your account password will NOT work.
echo ==========================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] git is not installed.
  pause
  exit /b 1
)

if not exist ".git" (
  git init >nul
  git symbolic-ref HEAD refs/heads/main
  git remote add space https://huggingface.co/spaces/yellowmug/mindily
)
git remote set-url space https://huggingface.co/spaces/yellowmug/mindily

echo [1/5] Fetching the current Space...
git -c credential.helper= -c credential.interactive=never fetch space main
if errorlevel 1 (
  echo [ERROR] Could not reach the Space. Check the network and try again.
  pause
  exit /b 1
)

echo [2/5] Comparing with local files...
git reset --soft space/main
git checkout space/main -- .gitattributes

echo [3/5] Staging changes...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git diff --cached --name-status
  echo.
  echo [4/5] Committing...
  git -c user.name="80gina" -c user.email="rkwktkeo20@gmail.com" commit -q -m "Sync app update: installable app, comfort content, healing tabs"
) else (
  echo [OK] Files already match the Space. Nothing new to commit.
)

git log space/main..HEAD --oneline >nul 2>&1
git rev-list --count space/main..HEAD > "%TEMP%\hfahead.txt"
set /p AHEAD=<"%TEMP%\hfahead.txt"
del "%TEMP%\hfahead.txt" >nul 2>&1
if "%AHEAD%"=="0" (
  echo [DONE] The Space is already up to date.
  pause
  exit /b 0
)

echo.
echo [5/5] Uploading...
echo.
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "$s = Read-Host -AsSecureString 'Paste your Hugging Face WRITE token (typing stays hidden)'; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))"`) do set "HFTOKEN=%%T"

if "%HFTOKEN%"=="" (
  echo [ERROR] No token entered.
  pause
  exit /b 1
)

git -c credential.helper= -c credential.interactive=never push https://yellowmug:%HFTOKEN%@huggingface.co/spaces/yellowmug/mindily main
set "RC=%ERRORLEVEL%"
set "HFTOKEN="

if not "%RC%"=="0" (
  echo.
  echo [ERROR] Upload failed.
  echo   - The token must be type WRITE. A Read token cannot upload.
  echo   - A fine-grained token needs write access to this Space repo.
  echo   - Copy the whole token. It starts with hf_ .
  pause
  exit /b 1
)

echo.
echo [DONE] Uploaded. Open the Space and check the Logs tab:
echo   https://huggingface.co/spaces/yellowmug/mindily
pause

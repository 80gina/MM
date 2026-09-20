@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0_space_upload"

echo ==========================================================
echo   Hugging Face Space upload  -  yellowmug/mindily
echo ----------------------------------------------------------
echo   If a login window appears:
echo     Username : yellowmug
echo     Password : your Hugging Face WRITE token
echo                (https://huggingface.co/settings/tokens)
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
git fetch space main
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
if not errorlevel 1 (
  echo [OK] The Space is already up to date. Nothing to upload.
  pause
  exit /b 0
)

git diff --cached --name-status

echo.
echo [4/5] Committing...
git -c user.name="80gina" -c user.email="rkwktkeo20@gmail.com" commit -m "Sync app update: installable app, comfort content, healing tabs"

echo [5/5] Uploading...
git push space main
if errorlevel 1 (
  echo.
  echo [ERROR] Upload failed.
  echo   - Use a WRITE token as the password, not your account password.
  echo   - If an old wrong token is saved: Windows Credential Manager
  echo     -^> Windows Credentials -^> delete git:https://huggingface.co
  pause
  exit /b 1
)

echo.
echo [DONE] Uploaded. Open the Space and check the Logs tab:
echo   https://huggingface.co/spaces/yellowmug/mindily
pause

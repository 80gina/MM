@echo off
setlocal
set "ROOT=%~dp0"
set "TMP=%TEMP%\mindily-hf-upload-%RANDOM%"

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

echo [1/5] Fetching the current Space...
git clone https://huggingface.co/spaces/yellowmug/mindily "%TMP%"
if errorlevel 1 (
  echo [ERROR] Could not reach the Space. Check the network and try again.
  pause
  exit /b 1
)

echo [2/5] Copying the current MM source files...
copy /Y "%ROOT%Dockerfile" "%TMP%\Dockerfile" >nul
copy /Y "%ROOT%requirements.txt" "%TMP%\requirements.txt" >nul
copy /Y "%ROOT%server.py" "%TMP%\server.py" >nul
copy /Y "%ROOT%coach_agent.py" "%TMP%\coach_agent.py" >nul
copy /Y "%ROOT%rag.py" "%TMP%\rag.py" >nul
copy /Y "%ROOT%llm.py" "%TMP%\llm.py" >nul
copy /Y "%ROOT%diary_draft.py" "%TMP%\diary_draft.py" >nul
copy /Y "%ROOT%feedback_db.py" "%TMP%\feedback_db.py" >nul
copy /Y "%ROOT%healing_knowledge.py" "%TMP%\healing_knowledge.py" >nul
copy /Y "%ROOT%memory_db.py" "%TMP%\memory_db.py" >nul
copy /Y "%ROOT%SPACE_README.md" "%TMP%\README.md" >nul
if exist "%TMP%\dist" rmdir /S /Q "%TMP%\dist"
xcopy "%ROOT%dist" "%TMP%\dist" /E /I /Y >nul

pushd "%TMP%"
for /f "delims=" %%H in ('git rev-parse HEAD') do set "BASE_COMMIT=%%H"
echo [3/5] Staging changes...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git diff --cached --name-status
  echo.
  echo [4/5] Committing...
  git -c user.name="80gina" -c user.email="rkwktkeo20@gmail.com" commit -q -m "Sync Mindily app update"
) else (
  echo [OK] Files already match the Space. Nothing new to commit.
)

for /f "delims=" %%H in ('git rev-parse HEAD') do set "NEW_COMMIT=%%H"
if "%BASE_COMMIT%"=="%NEW_COMMIT%" (
  echo [DONE] The Space is already up to date.
  popd
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

git push https://yellowmug:%HFTOKEN%@huggingface.co/spaces/yellowmug/mindily main
set "RC=%ERRORLEVEL%"
set "HFTOKEN="
popd

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

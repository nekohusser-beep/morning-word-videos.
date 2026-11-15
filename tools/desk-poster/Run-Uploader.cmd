@echo off
REM desk-poster: uploads + schedules every video waiting in Desktop\Claude-Work\desk-poster\queue
REM First time: Run-Uploader.cmd login  (sign in to Blessed Prayers once in the window that opens)
setlocal
set HOME_DIR=%USERPROFILE%\Desktop\Claude-Work\desk-poster
if not exist "%HOME_DIR%\queue" mkdir "%HOME_DIR%\queue"
cd /d "%HOME_DIR%"
where py >nul 2>nul && (set PY=py -3) || (where python >nul 2>nul && (set PY=python) || (winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements & set PY=py -3))
%PY% -m pip install -q --upgrade playwright >> setup.log 2>&1
%PY% -m playwright install chromium >> setup.log 2>&1
curl -sL -o yt_studio_upload.py https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/desk-poster/yt_studio_upload.py
if /i "%1"=="login" (%PY% yt_studio_upload.py --login) else (%PY% yt_studio_upload.py)
echo Done. Results are in %HOME_DIR%\queue\done  (log: uploader.log)
timeout /t 15

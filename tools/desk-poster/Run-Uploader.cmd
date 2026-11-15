@echo off
REM desk-poster: uploads + schedules queued videos to Blessed Prayers. Double-click = sign in the first time, then uploads.
setlocal
set HOME_DIR=%USERPROFILE%\Desktop\Claude-Work\desk-poster
if not exist "%HOME_DIR%\queue" mkdir "%HOME_DIR%\queue"
cd /d "%HOME_DIR%"
copy /y "%~f0" "%HOME_DIR%\Run-Uploader.cmd" >nul 2>nul
where py >nul 2>nul && (set PY=py -3) || (where python >nul 2>nul && (set PY=python) || (winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements & set PY=py -3))
REM one-time disk cleanup: the drive was full (Nov 15). Uses your real Chrome, so Playwright's own browsers are not needed.
if not exist cleanup-done.txt (
  echo Freeing disk space, one time...
  rmdir /s /q "%LOCALAPPDATA%\ms-playwright" 2>nul
  %PY% -m pip cache purge >nul 2>nul
  del /f /s /q "%TEMP%\*" >nul 2>nul
  for /d %%D in ("%TEMP%\*") do rmdir /s /q "%%D" 2>nul
  echo done> cleanup-done.txt
)
if not exist "%USERPROFILE%\Desktop\Claude-Work\disk-report.txt" (echo Checking what fills the drive, 1-3 minutes... & curl -sL -o disk-report.ps1 https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/desk-poster/disk-report.ps1 & powershell -NoProfile -ExecutionPolicy Bypass -File "%HOME_DIR%\disk-report.ps1")
%PY% -c "import playwright" >nul 2>nul || (echo Installing the uploader, one time... & %PY% -m pip install -q --no-cache-dir playwright >> setup.log 2>&1)
curl -sL -o yt_studio_upload.py.new https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/desk-poster/yt_studio_upload.py && findstr /c:"signed_in.txt" yt_studio_upload.py.new >nul && move /y yt_studio_upload.py.new yt_studio_upload.py >nul
curl -sL -o Stop-Allow-Prompts.ps1 https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/desk-poster/Stop-Allow-Prompts.ps1
if not exist allow-done.txt (powershell -NoProfile -ExecutionPolicy Bypass -File "%HOME_DIR%\Stop-Allow-Prompts.ps1" && echo done> allow-done.txt)
REM every 30 minutes on its own from now on (no admin needed)
schtasks /query /tn DeskPoster >nul 2>nul || schtasks /create /tn DeskPoster /sc minute /mo 30 /tr "cmd /c \"%HOME_DIR%\Run-Uploader.cmd\" auto" /f >> setup.log 2>&1
if /i "%1"=="auto" (%PY% yt_studio_upload.py --auto & goto :end)
echo Opening Chrome...
if /i "%1"=="login" (%PY% yt_studio_upload.py --login & goto :end)
%PY% yt_studio_upload.py
:end
if /i not "%1"=="auto" timeout /t 15

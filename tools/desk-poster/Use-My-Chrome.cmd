@echo off
REM Reuses your Chrome's Blessed Prayers sign-in for the uploader. No new sign-in.
cd /d "%USERPROFILE%\Desktop\Claude-Work\desk-poster"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*yt_studio_upload*' -or $_.CommandLine -like '*Run-Uploader*' -or $_.CommandLine -like '*disk-report.ps1*' } | % { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% -c "import playwright" >nul 2>nul || %PY% -m pip install -q --no-cache-dir playwright
%PY% from_chrome.py
timeout /t 20

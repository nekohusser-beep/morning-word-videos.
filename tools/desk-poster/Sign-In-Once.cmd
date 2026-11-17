@echo off
REM Opens the uploader's own Chrome window on YouTube sign-in. Sign in to Blessed Prayers once; it stays signed in.
cd /d "%USERPROFILE%\Desktop\Claude-Work\desk-poster"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*yt_studio_upload*' -or $_.CommandLine -like '*Run-Uploader*' -or $_.CommandLine -like '*disk-report.ps1*' -or $_.CommandLine -like '*from_chrome*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
tasklist /FI "IMAGENAME eq chrome.exe" /NH | find /i "chrome.exe" >nul || start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --restore-last-session
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo Opening the uploader's Chrome window on YouTube Studio sign-in...
%PY% yt_studio_upload.py --login

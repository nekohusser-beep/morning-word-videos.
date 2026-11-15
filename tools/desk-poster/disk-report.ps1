$out = "$env:USERPROFILE\Desktop\Claude-Work\disk-report.txt"
function Size($p){ try { (Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } catch { 0 } }
$rows = @()
$targets = @()
$targets += Get-ChildItem -Force -Directory $env:USERPROFILE -ErrorAction SilentlyContinue | % FullName
$targets += Get-ChildItem -Force -Directory "$env:LOCALAPPDATA" -ErrorAction SilentlyContinue | % FullName
$targets += Get-ChildItem -Force -Directory "$env:APPDATA" -ErrorAction SilentlyContinue | % FullName
$targets += "C:\ProgramData","C:\Windows\Temp","C:\Windows\SoftwareDistribution\Download",'C:\$Recycle.Bin',"C:\Program Files","C:\Program Files (x86)"
foreach($t in ($targets | Select-Object -Unique)){ if($t -like "*\AppData"){continue}; $rows += [pscustomobject]@{GB=[math]::Round((Size $t)/1GB,2); Path=$t} }
$big = Get-ChildItem C:\Users\nekoh -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object Length -gt 500MB | Sort-Object Length -Descending | Select-Object -First 40 @{n='GB';e={[math]::Round($_.Length/1GB,2)}},FullName,LastWriteTime
$d = Get-PSDrive C
"FREE GB: {0:N2} of {1:N2}" -f ($d.Free/1GB), (($d.Used+$d.Free)/1GB) | Out-File $out -Encoding utf8
"`n=== FOLDERS ===" | Out-File $out -Append -Encoding utf8
$rows | Sort-Object GB -Descending | Select-Object -First 60 | Format-Table -AutoSize | Out-String -Width 300 | Out-File $out -Append -Encoding utf8
"`n=== FILES OVER 500 MB ===" | Out-File $out -Append -Encoding utf8
$big | Format-Table -AutoSize | Out-String -Width 400 | Out-File $out -Append -Encoding utf8
"DONE" | Out-File $out -Append -Encoding utf8

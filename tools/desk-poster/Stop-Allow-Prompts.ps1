# Sets Claude Code (laptop Code tab + CLI) to work without "Allow" prompts. Neko asked Nov 15 2026.
$dir = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$f = Join-Path $dir "settings.json"
if (Test-Path $f) { Copy-Item $f "$f.bak" -Force; $s = Get-Content $f -Raw | ConvertFrom-Json } else { $s = New-Object PSObject }
if (-not $s) { $s = New-Object PSObject }
$perm = [ordered]@{
  defaultMode = "bypassPermissions"
  allow = @("Bash","Edit","Write","MultiEdit","NotebookEdit","Read","Glob","Grep","WebFetch","WebSearch","TodoWrite","Task","Agent","Skill")
  deny  = @("Bash(rm -rf /:*)","Bash(rm -rf ~:*)","Bash(git push --force:*)")
}
$s | Add-Member -NotePropertyName permissions -NotePropertyValue $perm -Force
$s | Add-Member -NotePropertyName skipDangerousModePermissionPrompt -NotePropertyValue $true -Force
[IO.File]::WriteAllText($f, ($s | ConvertTo-Json -Depth 20))
Write-Host "Allow prompts off for Claude Code: $f"

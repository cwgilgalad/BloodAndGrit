# One-time setup: registers the "BloodAndGrit AutoSync" scheduled task
# (every 30 minutes + at logon, running autosync.ps1). Safe to re-run.
# Paths are derived from this script's own location, so it self-configures
# wherever the repo lives — no machine-specific paths to keep in sync.
# NOTE: run from an elevated PowerShell the first time; a non-elevated
# overwrite of an existing task is denied.
$pwsh   = (Get-Command pwsh).Source
$script = Join-Path $PSScriptRoot 'autosync.ps1'
$a  = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
$t1 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 30)
$t2 = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName 'BloodAndGrit AutoSync' -Action $a -Trigger $t1, $t2 `
    -Description 'Commits & pushes Blood & Grit changes to GitHub every 30 minutes (branch-aware)' -Force
Get-ScheduledTask -TaskName 'BloodAndGrit AutoSync' | Select-Object TaskName, State

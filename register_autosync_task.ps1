# One-time setup: registers the "<folder name> AutoSync" scheduled task
# (every 30 minutes + at logon, running autosync.ps1). Safe to re-run.
# Canonical copy, identical in every Desktop\Git repo — the task name and all
# paths derive from this script's own folder, so it self-configures wherever
# the repo lives; no machine- or repo-specific values to keep in sync.
# NOTE: run from an elevated PowerShell the first time; a non-elevated
# overwrite of an existing task is denied.
$name   = "$(Split-Path $PSScriptRoot -Leaf) AutoSync"
$pwsh   = (Get-Command pwsh).Source
$script = Join-Path $PSScriptRoot 'autosync.ps1'
$a  = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
$t1 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 30)
$t2 = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName $name -Action $a -Trigger $t1, $t2 `
    -Description 'Auto-commits repo changes every 30 minutes (branch-aware); pushes to GitHub only when an origin remote exists.' -Force
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State

# Blood & Grit — auto-sync local changes to GitHub.
# Run by the "BloodAndGrit AutoSync" scheduled task (every 30 min + at logon).
# Safe to run any time: does nothing until an 'origin' remote exists, and
# never discards local work (rebase with autostash; failures leave the repo as-is).

$repo = "C:\Users\Cole\Desktop\BloodAndGrit"
$log  = Join-Path $repo "autosync.log"
Set-Location $repo

function Say($m) { Add-Content $log "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" }

git remote get-url origin *> $null
if ($LASTEXITCODE -ne 0) { exit 0 }   # not wired to GitHub yet — quietly stand down

git add -A *> $null
$dirty = git status --porcelain
if ($dirty) {
    git -c user.name="Cole Williams" -c user.email="colewilliams@gmail.com" `
        commit -m "autosync: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" *> $null
    Say "committed $((@($dirty)).Count) changed path(s)"
}

git pull --rebase --autostash origin main *> $null
if ($LASTEXITCODE -ne 0) { Say "pull --rebase failed — leaving local state untouched"; exit 1 }

git push origin main *> $null
if ($LASTEXITCODE -ne 0) { Say "push failed (offline or auth?)"; exit 1 }
if ($dirty) { Say "pushed to origin/main" }

# keep the log from growing forever
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 256KB)) {
    Get-Content $log -Tail 200 | Set-Content $log
}

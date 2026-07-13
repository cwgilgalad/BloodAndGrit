# Blood & Grit — auto-sync local changes to GitHub.
# Run by the "BloodAndGrit AutoSync" scheduled task (every 30 min + at logon).
# Safe to run any time: does nothing until an 'origin' remote exists, and
# never discards local work (rebase with autostash; failures leave the repo as-is).
#
# Branch-aware (2026-07-12): commits and pushes WHATEVER branch is checked out,
# so session branches (session/<date>-<topic>) are backed up to GitHub the same
# as main. First push of a new branch sets its upstream automatically.

$repo = "C:\Users\Cole\Desktop\BloodAndGrit"
$log  = Join-Path $repo "autosync.log"
Set-Location $repo

function Say($m) { Add-Content $log "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" }

git remote get-url origin *> $null
if ($LASTEXITCODE -ne 0) { exit 0 }   # not wired to GitHub yet — quietly stand down

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -eq 'HEAD') { Say "detached HEAD — standing down"; exit 0 }

git add -A *> $null
$dirty = git status --porcelain
if ($dirty) {
    git -c user.name="Cole Williams" -c user.email="colewilliams@gmail.com" `
        commit -m "autosync($branch): $(Get-Date -Format 'yyyy-MM-dd HH:mm')" *> $null
    Say "committed $((@($dirty)).Count) changed path(s) on $branch"
}

# rebase onto the branch's own remote counterpart, if one exists yet
git ls-remote --exit-code --heads origin $branch *> $null
if ($LASTEXITCODE -eq 0) {
    git pull --rebase --autostash origin $branch *> $null
    if ($LASTEXITCODE -ne 0) { Say "pull --rebase failed on $branch — leaving local state untouched"; exit 1 }
}

git push -u origin $branch *> $null
if ($LASTEXITCODE -ne 0) { Say "push failed on $branch (offline or auth?)"; exit 1 }
if ($dirty) { Say "pushed to origin/$branch" }

# keep the log from growing forever
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 256KB)) {
    Get-Content $log -Tail 200 | Set-Content $log
}

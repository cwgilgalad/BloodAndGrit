# Auto-sync local changes — canonical copy, identical in every Desktop\Git repo.
# Run by the "<folder name> AutoSync" scheduled task (every 30 min + at logon).
# Safe to run any time: never discards local work (rebase with autostash;
# failures leave the repo as-is).
#
# Branch-aware, and curated-history-safe:
#   * On session/<date>-<topic> scratch branches it AUTO-COMMITS + pushes — WIP
#     backup is the whole point of a scratch branch.
#   * On main (and any other non-session branch) it NEVER fabricates a commit —
#     that pollutes curated history and races your own deliberate commits — it
#     only PUSHES the commits you made yourself, so real work is still backed up.
# So: work on a session branch when you want continuous WIP backup; work on main
# when you want to own every commit. First push of a new branch sets upstream.
#
# Local-only repos (no 'origin' remote — e.g. HRHS Scripts, by design) skip the
# pull/push; a session branch there still gets its local auto-commit.

# Repo root = this script's own folder, so it survives moving the repo.
$repo = $PSScriptRoot
$log  = Join-Path $repo "autosync.log"
Set-Location $repo

function Say($m) { Add-Content $log "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" }

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -eq 'HEAD') { Say "detached HEAD — standing down"; exit 0 }

# Scratch branches get an auto-commit of the working tree; curated branches (main
# and the like) do not — we only back up commits you made deliberately.
$dirty = $null
if ($branch -like 'session/*') {
    git add -A *> $null
    $dirty = git status --porcelain
    if ($dirty) {
        git -c user.name="Cole Williams" -c user.email="colewilliams@gmail.com" `
            commit -m "autosync($branch): $(Get-Date -Format 'yyyy-MM-dd HH:mm')" *> $null
        Say "committed $((@($dirty)).Count) changed path(s) on $branch"
    }
}

git remote get-url origin *> $null
if ($LASTEXITCODE -ne 0) {
    # local-only repo — commit stays local, nothing to push
    if ($dirty) { Say "local-only repo (no origin) — commit kept local" }
}
else {
    $treeClean = -not (git status --porcelain)
    # Reconcile with the remote branch only when the tree is clean — never autostash
    # your live edits out from under you on a curated branch you're working in.
    git ls-remote --exit-code --heads origin $branch *> $null
    if ($LASTEXITCODE -eq 0 -and $treeClean) {
        git pull --rebase --autostash origin $branch *> $null
        if ($LASTEXITCODE -ne 0) { Say "pull --rebase failed on $branch — leaving local state untouched"; exit 1 }
    }
    # Push whatever commits exist — your deliberate ones on main, the auto-commit on a
    # session branch. A push touches no working files, so it's safe with WIP present.
    git push -u origin $branch *> $null
    if ($LASTEXITCODE -ne 0) { Say "push failed on $branch (offline, auth, or needs a manual pull)"; exit 1 }
    if ($dirty) { Say "pushed to origin/$branch" }
}

# keep the log from growing forever
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 256KB)) {
    Get-Content $log -Tail 200 | Set-Content $log
}

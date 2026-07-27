<#
    package.ps1 — assemble GritKeeper.zip for a GitHub Release.

    Run this AFTER you have signed the published exe. The zip must carry the SIGNED binary,
    so signing comes first; this script only assembles and compresses. It folds in the
    re-mirror step (per CLAUDE.md) so the source copy in the deliverable can never be skipped.

    The usual flow for a release:
        1.  cd GK\source; dotnet publish -c Release        # produces the self-contained exe
        2.  <your sign step>  (sign.ps1 / signtool with your .pfx)  on the published exe
        3.  .\package.ps1                                   # this script -> GritKeeper.zip
        4.  upload GritKeeper.zip to the GitHub Release, paste RELEASE_NOTES_vX.Y.Z.md
            (a local scratch file — git-ignored, like the zip; the text lives on the Release)

    -Exe    path to the (signed) published exe; defaults to the standard publish output.
    -Force  package even if the exe is not Authenticode-signed (for a local test build only).
    -Staged build the zip from a temporary tree without touching GritKeeper\app. Use when a copy
            of GritKeeper is running from the delivered folder and holds its exe. The zip is
            identical either way; only the on-disk GritKeeper\app is left at its old build.

    If GritKeeper is running from GritKeeper\app, this script says so by name and switches to
    -Staged of its own accord rather than dying on a file lock. Closing that instance and
    re-running brings the delivered folder back up to date.
#>
param(
    [string] $Exe = "GK\source\bin\Release\net8.0-windows\win-x64\publish\GritKeeper.exe",
    [switch] $Force,
    [switch] $Staged
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

if (-not (Test-Path $Exe)) {
    throw "No exe at '$Exe'. Run 'dotnet publish -c Release' in GK\source first."
}

# --- report what we're about to ship, and refuse to package an unsigned build unless forced ---
$info = (Get-Item $Exe).VersionInfo
$sig  = (Get-AuthenticodeSignature $Exe).Status
Write-Host "GritKeeper.exe  version $($info.FileVersion)  signature $sig"
if ($sig -ne "Valid" -and -not $Force) {
    throw "The exe is not signed ($sig). Sign it first, or re-run with -Force for a test build."
}

# --- 0. is a copy of the app running out of the folder we are about to overwrite? ---
# Copying over a running exe fails, and it used to fail as a raw Copy-Item access error two
# thirds of the way through a release. Name the process instead, and carry on into a staging
# tree so the zip still gets built — the running instance is never touched.
$appDir = Join-Path $root "GritKeeper\app"
$appExe = Join-Path $appDir "GritKeeper.exe"
$holders = @(Get-Process GritKeeper -ErrorAction SilentlyContinue |
             Where-Object { $_.Path -and $_.Path -eq $appExe })
if ($holders.Count -gt 0 -and -not $Staged) {
    $Staged = $true
    foreach ($h in $holders) {
        Write-Host "  GritKeeper is running from GritKeeper\app (pid $($h.Id), started $($h.StartTime.ToString('HH:mm')))."
    }
    Write-Host "  It holds GritKeeper\app\GritKeeper.exe, so that folder is left as it is."
    Write-Host "  Building the zip from a staging tree instead — the zip is unaffected."
    Write-Host "  Close that instance and re-run to bring GritKeeper\app up to date too."
}

# Where the deliverable is assembled: the real folder, or a scratch copy of it.
if ($Staged) {
    $stage = Join-Path ([IO.Path]::GetTempPath()) "gritkeeper-package"
    if (Test-Path $stage) { [IO.Directory]::Delete($stage, $true) }
    $dest = $stage
} else {
    $dest = Join-Path $root "GritKeeper"
}
$destApp = Join-Path $dest "app"
New-Item -ItemType Directory -Force -Path $destApp | Out-Null

# --- 1. the signed exe into the deliverable's app/ (its runtime session.json never ships) ---
Copy-Item $Exe (Join-Path $destApp "GritKeeper.exe") -Force
# Everything the app writes beside itself at runtime, out. session.json was already handled;
# prefs.json was NOT, and it shipped in v1.20.1 carrying the packager's own run mode with
# "Remember": true — so every download launched into someone else's table and never saw the
# chooser. Anything the exe drops here belongs to the machine that ran it, not to the release.
foreach ($dropping in "session.json", "prefs.json", "startup-error.txt", "selftest-report.txt") {
    Remove-Item (Join-Path $destApp $dropping) -ErrorAction SilentlyContinue
}
# Only when staging: the delivered folder already holds its own README, and copying it onto
# itself is an error rather than a no-op.
if ($Staged) { Copy-Item (Join-Path $root "GritKeeper\README.md") (Join-Path $dest "README.md") -Force }
Write-Host "  copied exe -> $(Split-Path -Leaf $dest)\app\"

# --- 2. re-mirror the source (overwrite, not sync-and-diff — CLAUDE.md) ---
robocopy "GK\source" (Join-Path $dest "source") /MIR /XD bin obj publish /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Write-Host "  re-mirrored GK\source -> $(Split-Path -Leaf $dest)\source"

# --- 3. zip the whole deliverable ---
$zip = Join-Path $root "GritKeeper.zip"
Remove-Item $zip -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $dest "*") -DestinationPath $zip -CompressionLevel Optimal
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "  wrote GritKeeper.zip ($mb MB)"

# The zip is the deliverable, so check it carries what it must before anyone uploads it.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [IO.Compression.ZipFile]::OpenRead($zip)
try {
    $names = $z.Entries.FullName
    foreach ($must in @("app/GritKeeper.exe", "README.md", "source/Core.cs", "source/Data/creatures.json")) {
        if ($names -notcontains $must) { throw "the zip is missing $must" }
    }
    # And nothing that belongs to this machine. A settings file that ships is worse than a
    # missing one: it silently configures somebody else's first run.
    $leaked = $names | Where-Object { $_ -match '^app/(?!GritKeeper\.exe$)' }
    if ($leaked) { throw "the zip carries runtime state it should not: $($leaked -join ', ')" }
    Write-Host "  zip carries the exe, the README, and the full source ($($names.Count) entries)"
    Write-Host "  app/ holds the exe and nothing else"
} finally { $z.Dispose() }

Write-Host ""
Write-Host "Ready: GritKeeper.zip carries GritKeeper.exe $($info.FileVersion) ($sig) + the full source."
Write-Host "Upload it to the GitHub Release with RELEASE_NOTES_v$($info.FileVersion -replace '\.0$','').md:"
Write-Host "  gh release create gritkeeper-v$($info.FileVersion -replace '\.0$','') GritKeeper.zip --notes-file RELEASE_NOTES_v$($info.FileVersion -replace '\.0$','').md"
if ($Staged) {
    Write-Host ""
    Write-Host "NOTE: built from staging — GritKeeper\app is still on its old build. The zip is correct." -ForegroundColor Yellow
}

# robocopy leaves a non-zero $LASTEXITCODE on success (1 = files copied); end clean so a
# caller or CI check doesn't read this run as a failure.
exit 0

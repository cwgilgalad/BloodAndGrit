<#
    package.ps1 — assemble GritKeeper.zip for a GitHub Release.

    Run this AFTER you have signed the published exe. The zip must carry the SIGNED binary,
    so signing comes first; this script only assembles and compresses. It folds in the
    re-mirror step (per CLAUDE.md) so the source copy in the deliverable can never be skipped.

    The usual flow for a release:
        1.  cd GK\source; dotnet publish -c Release        # produces the self-contained exe
        2.  <your sign step>  (sign.ps1 / signtool with your .pfx)  on the published exe
        3.  .\package.ps1                                   # this script -> GritKeeper.zip
        4.  upload GritKeeper.zip to the GitHub Release, paste RELEASE_NOTES_v1.16.1.md

    -Exe   path to the (signed) published exe; defaults to the standard publish output.
    -Force package even if the exe is not Authenticode-signed (for a local test build only).
#>
param(
    [string] $Exe = "GK\source\bin\Release\net8.0-windows\win-x64\publish\GritKeeper.exe",
    [switch] $Force
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

# --- 1. the signed exe into the deliverable's app/ (its runtime session.json never ships) ---
$app = Join-Path $root "GritKeeper\app"
New-Item -ItemType Directory -Force -Path $app | Out-Null
Copy-Item $Exe (Join-Path $app "GritKeeper.exe") -Force
Remove-Item (Join-Path $app "session.json") -ErrorAction SilentlyContinue
Write-Host "  copied exe -> GritKeeper\app\"

# --- 2. re-mirror the source (overwrite, not sync-and-diff — CLAUDE.md) ---
robocopy "GK\source" "GritKeeper\source" /MIR /XD bin obj publish /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Write-Host "  re-mirrored GK\source -> GritKeeper\source"

# --- 3. zip the whole deliverable ---
$zip = Join-Path $root "GritKeeper.zip"
Remove-Item $zip -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $root "GritKeeper\*") -DestinationPath $zip -CompressionLevel Optimal
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "  wrote GritKeeper.zip ($mb MB)"

Write-Host ""
Write-Host "Ready: GritKeeper.zip carries GritKeeper.exe $($info.FileVersion) ($sig) + the full source."
Write-Host "Upload it to the GitHub Release and paste RELEASE_NOTES_v1.16.1.md."

# robocopy leaves a non-zero $LASTEXITCODE on success (1 = files copied); end clean so a
# caller or CI check doesn't read this run as a failure.
exit 0

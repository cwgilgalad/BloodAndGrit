<#
    sign.ps1 — Authenticode-sign the published GritKeeper.exe.

    Uses PowerShell's native Set-AuthenticodeSignature (no Windows SDK / signtool needed),
    with the code-signing certificate from the CurrentUser store. Timestamps the signature so
    it stays valid past the cert's expiry; if no timestamp server is reachable it signs anyway
    and says so.

    Release flow:  dotnet publish -c Release  →  .\sign.ps1  →  .\package.ps1  →  upload the zip

    -Exe         the exe to sign; defaults to the standard publish output.
    -Thumbprint  choose a specific cert; omit to auto-pick the one code-signing cert in the store.
    -TimestampServer  RFC3161 URL; omit to use the default, or "" to skip timestamping.
#>
param(
    [string] $Exe = "GK\source\bin\Release\net10.0-windows\win-x64\publish\GritKeeper.exe",
    [string] $Thumbprint = "",
    [string] $TimestampServer = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path $Exe)) {
    throw "No exe at '$Exe'. Run 'dotnet publish -c Release' in GK\source first."
}

# --- pick the signing cert: by thumbprint if given, else the sole code-signing cert in the store ---
if ($Thumbprint) {
    $cert = Get-Item "Cert:\CurrentUser\My\$Thumbprint" -ErrorAction SilentlyContinue
    if (-not $cert) { throw "No cert with thumbprint $Thumbprint in CurrentUser\My." }
} else {
    $candidates = @(Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert)
    if ($candidates.Count -eq 0) { throw "No code-signing certificate in CurrentUser\My. Pass -Thumbprint or install one." }
    if ($candidates.Count -gt 1) { throw "Found $($candidates.Count) code-signing certs; pass -Thumbprint to choose one." }
    $cert = $candidates[0]
}
Write-Host "Signing $Exe"
Write-Host "  with: $($cert.Subject)  [$($cert.Thumbprint)]  expires $($cert.NotAfter.ToString('yyyy-MM-dd'))"

# --- sign, timestamped if we can reach a server, otherwise plainly ---
$res = $null
if ($TimestampServer) {
    try {
        $res = Set-AuthenticodeSignature -FilePath $Exe -Certificate $cert -HashAlgorithm SHA256 -TimestampServer $TimestampServer
    } catch {
        Write-Host "  timestamp server unreachable ($TimestampServer) — signing without a timestamp."
    }
}
if (-not $res) {
    $res = Set-AuthenticodeSignature -FilePath $Exe -Certificate $cert -HashAlgorithm SHA256
}

Write-Host "  status: $($res.Status)$(if ($res.TimeStamperCertificate) { ' (timestamped)' } else { ' (no timestamp)' })"
if ($res.Status -ne "Valid") { throw "Signing failed: $($res.StatusMessage)" }

Write-Host ""
Write-Host "Signed. Next: .\package.ps1  (assembles GritKeeper.zip with the signed exe)."
exit 0

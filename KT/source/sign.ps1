# Authenticode-sign the published GritKeeper exe as "Cole Williams".
#
# Why: an unsigned, unknown-publisher exe is what Windows SmartScreen, Defender, and
# third-party agents (Cortex, firewalls) flag first. Signing + a timestamp + honest
# assembly metadata (see the csproj) removes the "unknown publisher" class of warning
# on any machine that trusts the certificate.
#
# What this does:
#   1. Finds (or creates, once) a self-signed code-signing certificate CN=Cole Williams
#      in CurrentUser\My. Reused on every run — do NOT mint a new cert per release, or
#      each release looks like a different publisher.
#   2. Installs it into THIS machine's LocalMachine Root + TrustedPublisher stores so
#      local runs are fully trusted (requires elevation; skipped silently if present).
#   3. Signs the exe with SHA-256 and an RFC3161 timestamp, then verifies.
#
# Honest limits: a self-signed certificate is only trusted where step 2 has been done.
# On other machines the file is still *signed by Cole Williams* (no more "unknown
# publisher — unsigned"), but SmartScreen reputation only fully clears with a
# CA-issued code-signing certificate. If you buy one, import it and this script will
# prefer it automatically (it picks the newest valid code-signing cert by CN).
#
# Usage:  .\sign.ps1 [-Path <exe>]     (defaults to the publish output)
param(
    [string]$Path = (Join-Path $PSScriptRoot 'bin\Release\net8.0-windows\win-x64\publish\GritKeeper.exe')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Path)) { throw "Not found: $Path — run 'dotnet publish -c Release' first." }

$cn = 'CN=Cole Williams'
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object Subject -eq $cn |
        Where-Object { $_.NotAfter -gt (Get-Date) } |
        Sort-Object NotAfter -Descending | Select-Object -First 1
if (-not $cert) {
    Write-Host "No code-signing certificate for $cn — creating one (valid 10 years)."
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $cn `
        -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 `
        -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddYears(10) `
        -FriendlyName 'Cole Williams code signing (Blood & Grit tools)'
}
Write-Host "Signing with: $($cert.Subject)  thumbprint $($cert.Thumbprint)  expires $($cert.NotAfter.ToShortDateString())"

# trust it on this machine (idempotent; needs an elevated shell the first time)
foreach ($store in 'Root', 'TrustedPublisher') {
    $present = Get-ChildItem "Cert:\LocalMachine\$store" | Where-Object Thumbprint -eq $cert.Thumbprint
    if (-not $present) {
        try {
            $s = New-Object System.Security.Cryptography.X509Certificates.X509Store($store, 'LocalMachine')
            $s.Open('ReadWrite'); $s.Add($cert); $s.Close()
            Write-Host "Installed into LocalMachine\$store."
        } catch { Write-Warning "Could not install into LocalMachine\$store (not elevated?): $_" }
    }
}

$r = Set-AuthenticodeSignature -FilePath $Path -Certificate $cert -HashAlgorithm SHA256 `
        -TimestampServer 'http://timestamp.digicert.com'
$check = Get-AuthenticodeSignature -FilePath $Path
Write-Host "Signature status: $($check.Status) — $($check.StatusMessage)"
# 'Valid' requires the trust-store install above; a signed-but-locally-untrusted file
# reports 'UnknownError'. Refuse to call anything but Valid a success.
if ($check.Status -ne 'Valid') { throw "Signature is not Valid on this machine. Aborting." }
Write-Host "Signed and verified: $Path"

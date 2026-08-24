$ErrorActionPreference = "Stop"

$cerPath = Join-Path $PSScriptRoot "certificates\code-signing.cer"

if (-not (Test-Path $cerPath)) {
    Write-Error "Certificate file not found at $cerPath. Please run create-certificate.ps1 first."
    exit 1
}

Write-Host "[Signing] Installing certificate to CurrentUser\TrustedPeople..."
Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\CurrentUser\TrustedPeople" | Out-Null

Write-Host "[Signing] Certificate installed successfully."
Write-Host "Local builds signed with this certificate will now be trusted on this computer."

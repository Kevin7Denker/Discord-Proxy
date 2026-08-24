param (
    [string]$PublisherName = "Kevin Denker",
    [int]$KeyLength = 3072,
    [int]$ValidityYears = 3,
    [securestring]$PfxPassword = $null
)

$ErrorActionPreference = "Stop"

$subject = "CN=$PublisherName"
$certDir = Join-Path $PSScriptRoot "certificates"
$cerPath = Join-Path $certDir "code-signing.cer"
$pfxPath = Join-Path $certDir "code-signing.pfx"
$thumbprintFile = Join-Path $PSScriptRoot "thumbprint.txt"

if (-not (Test-Path $certDir)) {
    New-Item -ItemType Directory -Force -Path $certDir | Out-Null
}

Write-Host "[Signing] Checking for existing certificates for $subject..."
$existingCert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object {
    $_.Subject -eq $subject -and 
    $_.HasPrivateKey -and 
    $_.EnhancedKeyUsageList.FriendlyName -contains "Code Signing" -and
    $_.NotAfter -gt (Get-Date)
} | Sort-Object NotAfter -Descending | Select-Object -First 1

if ($existingCert) {
    Write-Host "[Signing] Valid certificate found with Thumbprint: $($existingCert.Thumbprint)"
    $cert = $existingCert
} else {
    Write-Host "[Signing] No valid certificate found. Creating a new self-signed certificate..."
    
    # Create the certificate
    $cert = New-SelfSignedCertificate -Subject $subject `
                                      -Type CodeSigningCert `
                                      -KeyAlgorithm RSA `
                                      -KeyLength $KeyLength `
                                      -HashAlgorithm SHA256 `
                                      -NotAfter (Get-Date).AddYears($ValidityYears) `
                                      -KeyExportPolicy Exportable `
                                      -CertStoreLocation "Cert:\CurrentUser\My"

    Write-Host "[Signing] New certificate created with Thumbprint: $($cert.Thumbprint)"
}

# Export public key (.cer)
Export-Certificate -Cert $cert -FilePath $cerPath -Force | Out-Null
Write-Host "[Signing] Public certificate exported to: $cerPath"

# Export private key (.pfx) if a password is provided
if ($PfxPassword) {
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $PfxPassword -Force | Out-Null
    Write-Host "[Signing] Private key exported to: $pfxPath"
} else {
    Write-Host "[Signing] PFX password not provided. Skipping .pfx export."
}

# Save Thumbprint to file for signing script
$cert.Thumbprint | Out-File -FilePath $thumbprintFile -Encoding ASCII -Force
Write-Host "[Signing] Thumbprint saved to $thumbprintFile"

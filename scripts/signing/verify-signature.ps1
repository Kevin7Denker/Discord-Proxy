param (
    [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
    [string[]]$FilesToVerify
)

$ErrorActionPreference = "Stop"

foreach ($file in $FilesToVerify) {
    if (-not (Test-Path $file)) {
        Write-Warning "[Verify] File not found: $file. Skipping."
        continue
    }

    Write-Host "[Verify] Verifying signature for $(Split-Path $file -Leaf)..."
    
    $sig = Get-AuthenticodeSignature -FilePath $file
    
    Write-Host "File: $($sig.Path)"
    Write-Host "Status: $($sig.StatusMessage)"
    
    if ($sig.SignerCertificate) {
        Write-Host "Subject: $($sig.SignerCertificate.Subject)"
        Write-Host "Issuer: $($sig.SignerCertificate.Issuer)"
        Write-Host "Thumbprint: $($sig.SignerCertificate.Thumbprint)"
        Write-Host "Valid From: $($sig.SignerCertificate.NotBefore)"
        Write-Host "Valid To: $($sig.SignerCertificate.NotAfter)"
    }
    
    if ($sig.TimeStamperCertificate) {
        Write-Host "Timestamped By: $($sig.TimeStamperCertificate.Subject)"
    } else {
        Write-Host "Timestamped By: None"
    }
    
    Write-Host "----------------------------------------"

    if ($sig.Status -eq "Valid") {
        Write-Host "[Verify] Signature valid." -ForegroundColor Green
    } else {
        Write-Error "[Verify] Signature invalid or missing for $file. Status: $($sig.Status)"
        exit 1
    }
}

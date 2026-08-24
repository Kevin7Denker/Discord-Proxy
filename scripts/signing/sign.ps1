param (
    [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
    [string[]]$FilesToSign
)

$ErrorActionPreference = "Stop"

$thumbprintFile = Join-Path $PSScriptRoot "thumbprint.txt"

if (-not (Test-Path $thumbprintFile)) {
    Write-Error "Thumbprint file not found. Please run create-certificate.ps1 first."
    exit 1
}

$thumbprint = Get-Content $thumbprintFile | Out-String | ForEach-Object { $_.Trim() }

Write-Host "[Signing] Thumbprint: $thumbprint"

# Locate signtool.exe
$sdkPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe"
)

$signtool = $null
foreach ($path in $sdkPaths) {
    $found = Resolve-Path $path -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path | Sort-Object -Descending | Select-Object -First 1
    if ($found) {
        $signtool = $found
        break
    }
}

if (-not $signtool) {
    Write-Error "signtool.exe not found. Please install the Windows SDK."
    exit 1
}

Write-Host "[Signing] Using SignTool: $signtool"

$timestampUrl = $env:TIMESTAMP_URL

foreach ($file in $FilesToSign) {
    if (-not (Test-Path $file)) {
        Write-Warning "[Signing] File not found: $file. Skipping."
        continue
    }

    Write-Host "[Signing] Signing $(Split-Path $file -Leaf)..."
    
    $signArgs = @(
        "sign",
        "/sha1", $thumbprint,
        "/fd", "SHA256"
    )

    if ($timestampUrl) {
        $signArgs += "/tr", $timestampUrl, "/td", "SHA256"
        Write-Host "[Signing] Using timestamp server: $timestampUrl"
    }

    $signArgs += $file

    $process = Start-Process -FilePath $signtool -ArgumentList $signArgs -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        Write-Error "[Signing] Failed to sign $file. Exit code: $($process.ExitCode)"
        exit 1
    }
    
    Write-Host "[Signing] Successfully signed $(Split-Path $file -Leaf)."
}

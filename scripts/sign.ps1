Param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path,

    [string]$CertificateThumbprint = $env:CODESIGN_CERT_THUMBPRINT,
    [string]$CertificateSubject = $env:CODESIGN_CERT_SUBJECT,
    [string]$TimestampServer = $(if ($env:CODESIGN_TIMESTAMP_SERVER) { $env:CODESIGN_TIMESTAMP_SERVER } else { "http://timestamp.digicert.com" }),
    [switch]$UseDevelopmentCertificate
)

$ErrorActionPreference = "Stop"

function Find-SignTool {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $kitsRoot = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
    if (Test-Path -LiteralPath $kitsRoot) {
        $candidate = Get-ChildItem -LiteralPath $kitsRoot -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($candidate) {
            return $candidate.FullName
        }
    }

    throw "SignTool not found. Install the Windows SDK or add signtool.exe to PATH."
}

function Normalize-Thumbprint([string]$Thumbprint) {
    return ($Thumbprint -replace "\s", "").ToUpperInvariant()
}

$target = Resolve-Path -LiteralPath $Path -ErrorAction Stop
$signTool = Find-SignTool

if ($UseDevelopmentCertificate) {
    Write-Warning "Using a self-signed development certificate. DO NOT use this for public releases."
    if (-not $CertificateSubject) {
        $CertificateSubject = "Discord Proxy Development"
    }
}

$args = @("sign", "/fd", "SHA256", "/tr", $TimestampServer, "/td", "SHA256")

if ($CertificateThumbprint) {
    $args += @("/sha1", (Normalize-Thumbprint $CertificateThumbprint))
} elseif ($CertificateSubject) {
    $args += @("/n", $CertificateSubject)
} else {
    throw "Configure CODESIGN_CERT_THUMBPRINT or CODESIGN_CERT_SUBJECT. For local-only testing, create a development certificate and pass -UseDevelopmentCertificate."
}

$args += $target.Path

Write-Host "Signing: $($target.Path)"
& $signTool @args
if ($LASTEXITCODE -ne 0) {
    throw "SignTool sign failed with exit code $LASTEXITCODE."
}

& $PSScriptRoot\verify-signature.ps1 $target.Path

Param(
    [string]$Configuration = "Production",
    [string]$InnoSetupCompiler = $env:INNOSETUP_COMPILER,
    [string]$AppExe = "dist\DiscordProxie\DiscordProxie.exe",
    [string]$SetupExe = "dist\DiscordProxie-Setup.exe"
)

$ErrorActionPreference = "Stop"

function Find-InnoSetupCompiler {
    Param([string]$ConfiguredPath)

    if ($ConfiguredPath -and (Test-Path -LiteralPath $ConfiguredPath)) {
        return (Resolve-Path -LiteralPath $ConfiguredPath).Path
    }

    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Inno Setup compiler not found. Install Inno Setup 6 or set INNOSETUP_COMPILER."
}

if ($Configuration -notin @("Production", "Development")) {
    throw "Configuration must be Production or Development."
}

Write-Host "Cleaning previous build output..."
if (Test-Path -LiteralPath "build") {
    Remove-Item -LiteralPath "build" -Recurse -Force
}
if (Test-Path -LiteralPath $AppExe) {
    Remove-Item -LiteralPath $AppExe -Force
}
if (Test-Path -LiteralPath $SetupExe) {
    Remove-Item -LiteralPath $SetupExe -Force
}

Write-Host "Building application..."
python scripts\build.py
if ($LASTEXITCODE -ne 0) {
    throw "Application build failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $AppExe)) {
    throw "Application executable not found: $AppExe"
}

Write-Host "Signing application executable..."
if ($Configuration -eq "Development") {
    & $PSScriptRoot\sign.ps1 $AppExe -UseDevelopmentCertificate
} else {
    & $PSScriptRoot\sign.ps1 $AppExe
}

$iscc = Find-InnoSetupCompiler -ConfiguredPath $InnoSetupCompiler
Write-Host "Building installer..."
& $iscc "scripts\installer.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $SetupExe)) {
    throw "Installer not found: $SetupExe"
}

Write-Host "Signing installer..."
if ($Configuration -eq "Development") {
    & $PSScriptRoot\sign.ps1 $SetupExe -UseDevelopmentCertificate
} else {
    & $PSScriptRoot\sign.ps1 $SetupExe
}

Write-Host "Release artifacts:"
Get-Item -LiteralPath $AppExe, $SetupExe | Select-Object FullName, Length, LastWriteTime

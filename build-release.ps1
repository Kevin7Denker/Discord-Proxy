$ErrorActionPreference = "Stop"

Write-Host "======================================"
Write-Host "     DISCORD PROXIE RELEASE BUILD"
Write-Host "======================================"
Write-Host ""

$pythonExe = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 1. Clean
Write-Host "[1/6] Cleaning previous builds..."
& $pythonExe scripts/clean.py
if ($LASTEXITCODE -ne 0) { Write-Error "Clean failed."; exit 1 }

# 2. Build via PyInstaller
Write-Host "`n[2/6] Building application..."
& $pythonExe scripts/build.py
if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }
Write-Host "Application built successfully."

# 3. Sign Executable
Write-Host "`n[3/6] Signing application executable..."
$exePath = ".\dist\DiscordProxie\DiscordProxie.exe"
.\scripts\signing\sign.ps1 $exePath

# 4. Build Setup via Inno Setup
Write-Host "`n[4/6] Building installer..."
$isccPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$iscc = $null
foreach ($path in $isccPaths) {
    if (Test-Path $path) {
        $iscc = $path
        break
    }
}

$setupPath = ".\dist\DiscordProxie-Setup.exe"

if ($iscc) {
    $process = Start-Process -FilePath $iscc -ArgumentList ".\scripts\installer.iss" -Wait -NoNewWindow -PassThru
    if ($process.ExitCode -ne 0) {
        Write-Error "Installer build failed. Exit code: $($process.ExitCode)"
        exit 1
    }
    Write-Host "Installer built successfully."
    
    # 5. Sign Installer
    Write-Host "`n[5/6] Signing installer..."
    .\scripts\signing\sign.ps1 $setupPath
    
    # 6. Verify Both
    Write-Host "`n[6/6] Verifying signatures..."
    .\scripts\signing\verify-signature.ps1 $exePath $setupPath
} else {
    Write-Warning "`n[4/6] Inno Setup (ISCC.exe) not found. Skipping installer generation."
    
    # 6. Verify Executable Only
    Write-Host "`n[6/6] Verifying signature..."
    .\scripts\signing\verify-signature.ps1 $exePath
    
    $setupPath = "(Setup not generated)"
}

Write-Host "`n======================================"
Write-Host "Release ready!"
Write-Host "Executable: $exePath"
if ($iscc) { Write-Host "Installer:  $setupPath" }
Write-Host "======================================"

Param(
    [string]$AppName = "DiscordProxy",
    [string]$MainFile = "main.py",
    [string]$VersionFile = "version_info.txt",
    [string]$IconFile = "assets/icon.ico"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MainFile)) {
    throw "Main file not found: $MainFile"
}

if (-not (Test-Path $VersionFile)) {
    throw "Version file not found: $VersionFile"
}

$venvPyInstaller = ".venv/Scripts/pyinstaller.exe"
if (Test-Path $venvPyInstaller) {
    $pyinstaller = $venvPyInstaller
} else {
    $pyinstaller = "pyinstaller"
}

$args = @(
    "--onefile",
    "--noconsole",
    "--clean",
    "--name", $AppName,
    "--version-file", $VersionFile,
    "--add-data", "assets;assets",
    "--add-data", "core;core",
    "--add-data", "ui;ui",
    $MainFile
)

if (Test-Path $IconFile) {
    $args = @("--icon", $IconFile) + $args
    Write-Host "Using icon: $IconFile"
} else {
    Write-Host "Icon not found ($IconFile). Building without icon."
}

Write-Host "Running PyInstaller..."
& $pyinstaller @args

Write-Host "Build complete. Output: dist/$AppName.exe"

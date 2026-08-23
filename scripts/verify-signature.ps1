Param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path
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

$target = Resolve-Path -LiteralPath $Path -ErrorAction Stop
$signature = Get-AuthenticodeSignature -LiteralPath $target.Path

if ($signature.Status -ne "Valid") {
    throw "Authenticode signature is not valid for $($target.Path). Status: $($signature.Status). $($signature.StatusMessage)"
}

$signTool = Find-SignTool
& $signTool verify /pa /v $target.Path
if ($LASTEXITCODE -ne 0) {
    throw "SignTool verify failed with exit code $LASTEXITCODE."
}

Write-Host "Signature valid: $($target.Path)"

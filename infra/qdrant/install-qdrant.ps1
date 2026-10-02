# Download qdrant.exe into %LOCALAPPDATA%\Qdrant (native Windows, ADR-0017).
# powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1
# powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1 -Version v1.15.5

param(
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

$qdrantHome = Join-Path $env:LOCALAPPDATA "Qdrant"
$qdrantExe = Join-Path $qdrantHome "qdrant.exe"
New-Item -ItemType Directory -Force -Path $qdrantHome | Out-Null

if (Test-Path $qdrantExe) {
    Write-Host "qdrant.exe already present: $qdrantExe"
    & $qdrantExe --version
    exit 0
}

$asset = "qdrant-x86_64-pc-windows-msvc.zip"
$url = if ($Version -eq "latest") {
    "https://github.com/qdrant/qdrant/releases/latest/download/$asset"
} else {
    "https://github.com/qdrant/qdrant/releases/download/$Version/$asset"
}

$zip = Join-Path $env:TEMP $asset
Write-Host "Downloading $url ..."
& curl.exe -L --fail --retry 3 --retry-delay 2 -o $zip $url
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zip)) {
    Write-Error "Failed to download $url"
}

Expand-Archive -Path $zip -DestinationPath $qdrantHome -Force
Remove-Item $zip -Force -ErrorAction SilentlyContinue

if (-not (Test-Path $qdrantExe)) {
    Write-Error "qdrant.exe not found after unzip in $qdrantHome"
}

Write-Host "Saved -> $qdrantExe"
& $qdrantExe --version
Write-Host ""
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\qdrant\start-qdrant.ps1"

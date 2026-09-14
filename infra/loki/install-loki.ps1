# Download Loki Windows binary into %LOCALAPPDATA%\Loki.
# powershell -ExecutionPolicy Bypass -File infra\loki\install-loki.ps1

$ErrorActionPreference = "Stop"

$lokiVersion = "3.7.7"
$lokiHome = Join-Path $env:LOCALAPPDATA "Loki"
$dataDir = Join-Path $lokiHome "data"
$zipPath = Join-Path $lokiHome "loki-windows-amd64.exe.zip"
$lokiExe = Join-Path $lokiHome "loki.exe"
$downloadUrl = "https://github.com/grafana/loki/releases/download/v$lokiVersion/loki-windows-amd64.exe.zip"

New-Item -ItemType Directory -Force -Path $lokiHome | Out-Null
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "chunks") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "rules") | Out-Null

if (Test-Path $lokiExe) {
    Write-Host "loki.exe already present: $lokiExe"
} else {
    Write-Host "Downloading Loki v$lokiVersion ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zipPath $downloadUrl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zipPath)) {
        Write-Error "Failed to download Loki from $downloadUrl"
    }

    $extractDir = Join-Path $lokiHome "_extract"
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $found = Get-ChildItem -Path $extractDir -Recurse -Filter "loki*.exe" |
        Where-Object { $_.Name -notmatch "canary|logcli|lokitool" } |
        Select-Object -First 1
    if (-not $found) {
        Write-Error "loki.exe not found inside $zipPath"
    }

    Move-Item -Force $found.FullName $lokiExe
    Remove-Item -Recurse -Force $extractDir
    Remove-Item -Force $zipPath
    Write-Host "Saved loki.exe -> $lokiExe"
}

Write-Host ""
Write-Host "Install dir: $lokiHome"
Write-Host "Data dir:    $dataDir"
Write-Host "Version:     $lokiVersion"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1"

# Download Prometheus Windows binaries into %LOCALAPPDATA%\Prometheus.
# powershell -ExecutionPolicy Bypass -File infra\prometheus\install-prometheus.ps1

$ErrorActionPreference = "Stop"

$promVersion = "3.14.0"
$promHome = Join-Path $env:LOCALAPPDATA "Prometheus"
$dataDir = Join-Path $promHome "data"
$zipPath = Join-Path $promHome "prometheus-windows-amd64.zip"
$promExe = Join-Path $promHome "prometheus.exe"
$promtoolExe = Join-Path $promHome "promtool.exe"
$downloadUrl = "https://github.com/prometheus/prometheus/releases/download/v$promVersion/prometheus-$promVersion.windows-amd64.zip"

New-Item -ItemType Directory -Force -Path $promHome | Out-Null
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if ((Test-Path $promExe) -and (Test-Path $promtoolExe)) {
    Write-Host "prometheus.exe already present: $promExe"
} else {
    Write-Host "Downloading Prometheus v$promVersion ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zipPath $downloadUrl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zipPath)) {
        Write-Error "Failed to download Prometheus from $downloadUrl"
    }

    $extractDir = Join-Path $promHome "_extract"
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $foundProm = Get-ChildItem -Path $extractDir -Recurse -Filter "prometheus.exe" | Select-Object -First 1
    $foundTool = Get-ChildItem -Path $extractDir -Recurse -Filter "promtool.exe" | Select-Object -First 1
    if (-not $foundProm) {
        Write-Error "prometheus.exe not found inside $zipPath"
    }

    Move-Item -Force $foundProm.FullName $promExe
    if ($foundTool) {
        Move-Item -Force $foundTool.FullName $promtoolExe
    }
    Remove-Item -Recurse -Force $extractDir
    Remove-Item -Force $zipPath
    Write-Host "Saved prometheus.exe -> $promExe"
    if (Test-Path $promtoolExe) {
        Write-Host "Saved promtool.exe  -> $promtoolExe"
    }
}

Write-Host ""
Write-Host "Install dir: $promHome"
Write-Host "Data dir:    $dataDir"
Write-Host "Version:     $promVersion"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1"

# Download Grafana OSS Windows binary into %LOCALAPPDATA%\Grafana.
# powershell -ExecutionPolicy Bypass -File infra\grafana\install-grafana.ps1

$ErrorActionPreference = "Stop"

$grafanaVersion = "13.2.1"
$grafanaHome = Join-Path $env:LOCALAPPDATA "Grafana"
$dataDir = Join-Path $grafanaHome "data"
$logDir = Join-Path $grafanaHome "log"
$pluginsDir = Join-Path $grafanaHome "plugins"
$zipPath = Join-Path $grafanaHome "grafana-windows-amd64.zip"
$downloadUrl = "https://dl.grafana.com/oss/release/grafana-$grafanaVersion.windows-amd64.zip"

function Find-GrafanaExe {
    param([string]$Root)
    $candidates = @(
        (Join-Path $Root "bin\grafana.exe"),
        (Join-Path $Root "bin\grafana-server.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    $found = Get-ChildItem -Path $Root -Recurse -Include "grafana.exe", "grafana-server.exe" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

New-Item -ItemType Directory -Force -Path $grafanaHome | Out-Null
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null

$existing = Find-GrafanaExe -Root $grafanaHome
if ($existing) {
    Write-Host "Grafana already present: $existing"
} else {
    Write-Host "Downloading Grafana OSS v$grafanaVersion (~450 MB) ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zipPath $downloadUrl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zipPath)) {
        Write-Error "Failed to download Grafana from $downloadUrl"
    }

    $extractDir = Join-Path $grafanaHome "_extract"
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Write-Host "Extracting archive ..."
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $inner = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if (-not $inner) {
        Write-Error "Unexpected archive layout in $zipPath"
    }

    # Move contents of grafana-VERSION/ into %LOCALAPPDATA%\Grafana\
    Get-ChildItem -Path $inner.FullName -Force | ForEach-Object {
        $dest = Join-Path $grafanaHome $_.Name
        if (Test-Path $dest) {
            Remove-Item -Recurse -Force $dest
        }
        Move-Item -Force $_.FullName $dest
    }

    Remove-Item -Recurse -Force $extractDir
    Remove-Item -Force $zipPath

    $existing = Find-GrafanaExe -Root $grafanaHome
    if (-not $existing) {
        Write-Error "grafana.exe not found after extract under $grafanaHome"
    }
    Write-Host "Saved Grafana -> $existing"
}

Write-Host ""
Write-Host "Install dir: $grafanaHome"
Write-Host "Data dir:    $dataDir"
Write-Host "Binary:      $(Find-GrafanaExe -Root $grafanaHome)"
Write-Host "Version:     $grafanaVersion"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\grafana\start-grafana.ps1"

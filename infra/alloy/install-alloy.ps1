# Download Grafana Alloy Windows binary into %LOCALAPPDATA%\Alloy.
# powershell -ExecutionPolicy Bypass -File infra\alloy\install-alloy.ps1

$ErrorActionPreference = "Stop"

$alloyVersion = "1.19.2"
$alloyHome = Join-Path $env:LOCALAPPDATA "Alloy"
$dataDir = Join-Path $alloyHome "data"
$zipPath = Join-Path $alloyHome "alloy-windows-amd64.exe.zip"
$alloyExe = Join-Path $alloyHome "alloy.exe"
$downloadUrl = "https://github.com/grafana/alloy/releases/download/v$alloyVersion/alloy-windows-amd64.exe.zip"

New-Item -ItemType Directory -Force -Path $alloyHome | Out-Null
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if (Test-Path $alloyExe) {
    Write-Host "alloy.exe already present: $alloyExe"
} else {
    Write-Host "Downloading Grafana Alloy v$alloyVersion ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zipPath $downloadUrl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zipPath)) {
        Write-Error "Failed to download Alloy from $downloadUrl"
    }

    $extractDir = Join-Path $alloyHome "_extract"
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $found = Get-ChildItem -Path $extractDir -Recurse -Filter "alloy*.exe" |
        Where-Object { $_.Name -notmatch "installer" } |
        Select-Object -First 1
    if (-not $found) {
        Write-Error "alloy.exe not found inside $zipPath"
    }

    Move-Item -Force $found.FullName $alloyExe
    Remove-Item -Recurse -Force $extractDir
    Remove-Item -Force $zipPath
    Write-Host "Saved alloy.exe -> $alloyExe"
}

Write-Host ""
Write-Host "Install dir: $alloyHome"
Write-Host "Data dir:    $dataDir"
Write-Host "Version:     $alloyVersion"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\alloy\start-alloy.ps1"

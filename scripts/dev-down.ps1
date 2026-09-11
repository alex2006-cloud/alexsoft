# Stop local pet-project services started by scripts\dev-up.ps1
# Stops Memurai, MinIO, and Landing (:3000).
# Does NOT stop PostgreSQL Windows service.
# Pass -SkipLanding to leave next dev running.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1 -SkipLanding

param(
    [switch]$SkipLanding
)

$ErrorActionPreference = "Continue"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$memuraiStop = Join-Path $env:LOCALAPPDATA "Memurai\stop-memurai.ps1"
$minioStop = Join-Path $repoRoot "infra\minio\stop-minio.ps1"

Write-Host "=== alexsoft local stack: stop ===" -ForegroundColor Cyan

if (Test-Path $memuraiStop) {
    Write-Host "[..] Stopping Memurai..."
    & powershell -ExecutionPolicy Bypass -File $memuraiStop
}
else {
    Get-Process -Name memurai -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "Memurai process stopped (no stop script)"
}

if (Test-Path $minioStop) {
    Write-Host "[..] Stopping MinIO..."
    & powershell -ExecutionPolicy Bypass -File $minioStop
}
else {
    Get-Process -Name minio -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "MinIO process stopped (no stop script)"
}

if (-not $SkipLanding) {
    Write-Host "[..] Stopping Landing (:3000)..."
    $listeners = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    if (-not $listeners) {
        Write-Host "Landing is not running on :3000"
    }
    else {
        foreach ($procId in $listeners) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process on :3000 (PID $procId)"
        }
    }
}
else {
    Write-Host "[--] Landing left running (-SkipLanding)" -ForegroundColor DarkYellow
}

Write-Host "=== done ===" -ForegroundColor Cyan

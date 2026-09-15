# Start local pet-project services that do NOT survive Windows reboot:
# PostgreSQL (if stopped), Memurai, MinIO, Landing (next dev).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1 -SkipLanding
#
# Stop: scripts\dev-down.ps1

param(
    [switch]$SkipLanding,
    [switch]$SkipGames
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$memuraiStart = Join-Path $env:LOCALAPPDATA "Memurai\start-memurai.ps1"
$minioStart = Join-Path $repoRoot "infra\minio\start-minio.ps1"

function Test-PortListen {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

Write-Host "=== alexsoft local stack ===" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot"
Write-Host ""

# --- PostgreSQL ---
$pg = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($pg) {
    if ($pg.Status -eq "Running") {
        Write-Host "[OK] PostgreSQL service already running (port 5432)" -ForegroundColor Green
    }
    else {
        Write-Host "[..] Starting PostgreSQL service..." -ForegroundColor Yellow
        Start-Service -Name "postgresql-x64-16"
        Start-Sleep -Seconds 2
        Write-Host "[OK] PostgreSQL started" -ForegroundColor Green
    }
}
else {
    Write-Host "[--] PostgreSQL service postgresql-x64-16 not found (skip)" -ForegroundColor DarkYellow
}

# --- Memurai (Redis) ---
Write-Host ""
Write-Host "[..] Memurai (Redis :6379)..." -ForegroundColor Yellow
if (-not (Test-Path $memuraiStart)) {
    Write-Error "Memurai start script not found: $memuraiStart (see infra/redis/README.md)"
}
if (Test-PortListen -Port 6379) {
    Write-Host "[OK] Memurai already listening on 6379" -ForegroundColor Green
}
else {
    & powershell -ExecutionPolicy Bypass -File $memuraiStart
    if (-not (Test-PortListen -Port 6379)) {
        Write-Error "Memurai did not open port 6379"
    }
    Write-Host "[OK] Memurai up" -ForegroundColor Green
}

# --- MinIO ---
Write-Host ""
Write-Host "[..] MinIO (S3 :9000, Console :9001)..." -ForegroundColor Yellow
if (-not (Test-Path $minioStart)) {
    Write-Error "MinIO start script not found: $minioStart"
}
& powershell -ExecutionPolicy Bypass -File $minioStart
if (-not (Test-PortListen -Port 9000)) {
    Write-Error "MinIO did not open port 9000"
}
Write-Host "[OK] MinIO up" -ForegroundColor Green

# --- Landing ---
if (-not $SkipLanding) {
    Write-Host ""
    Write-Host "[..] Landing (next dev :3000)..." -ForegroundColor Yellow
    $landingDir = Join-Path $repoRoot "apps\landing"
    if (-not (Test-Path (Join-Path $landingDir "package.json"))) {
        Write-Error "Landing app not found: $landingDir"
    }
    if (Test-PortListen -Port 3000) {
        Write-Host "[OK] Something already listens on 3000 - skip npm run dev" -ForegroundColor Green
    }
    else {
        $cmd = "Set-Location -LiteralPath '$landingDir'; npm run dev"
        Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command", $cmd
        )
        Write-Host "[OK] Landing started in a new terminal window" -ForegroundColor Green
    }
}
else {
    Write-Host ""
    Write-Host "[--] Landing skipped (-SkipLanding)" -ForegroundColor DarkYellow
}

# --- Games ---
if (-not $SkipGames) {
    Write-Host ""
    Write-Host "[..] Games (next dev :3010/games)..." -ForegroundColor Yellow
    $gamesDir = Join-Path $repoRoot "apps\games"
    if (-not (Test-Path (Join-Path $gamesDir "package.json"))) {
        Write-Error "Games app not found: $gamesDir"
    }
    if (Test-PortListen -Port 3010) {
        Write-Host "[OK] Something already listens on 3010 - skip npm run dev" -ForegroundColor Green
    }
    else {
        $cmd = "Set-Location -LiteralPath '$gamesDir'; npm run dev"
        Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command", $cmd
        )
        Write-Host "[OK] Games started in a new terminal window" -ForegroundColor Green
    }
}
else {
    Write-Host ""
    Write-Host "[--] Games skipped (-SkipGames)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== ready ===" -ForegroundColor Cyan
Write-Host "Redis:    127.0.0.1:6379"
Write-Host "MinIO:    http://127.0.0.1:9000"
Write-Host "Console:  http://127.0.0.1:9001"
Write-Host "Postgres: 127.0.0.1:5432"
if (-not $SkipLanding) {
    Write-Host "Landing:  http://127.0.0.1:3000"
}
if (-not $SkipGames) {
    Write-Host "Games:    http://127.0.0.1:3010/games"
}
Write-Host ""
$downScript = Join-Path $PSScriptRoot "dev-down.ps1"
Write-Host ("Stop with: powershell -ExecutionPolicy Bypass -File " + $downScript)

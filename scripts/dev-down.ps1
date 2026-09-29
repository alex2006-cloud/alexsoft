# Stop local services started by scripts\dev-up.ps1
# Does NOT stop PostgreSQL Windows service.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1 -SkipAi
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1 -WithObs -WithBi
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-down.ps1 -WithN8n -WithDify

param(
    [switch]$SkipAi,
    [switch]$SkipData,
    [switch]$WithLanding,
    [switch]$WithGames,
    [switch]$WithObs,
    [switch]$WithBi,
    [switch]$WithN8n,
    [switch]$WithDify
)

$ErrorActionPreference = "Continue"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$memuraiStop = Join-Path $env:LOCALAPPDATA "Memurai\stop-memurai.ps1"
$minioStop = Join-Path $repoRoot "infra\minio\stop-minio.ps1"
$litellmStop = Join-Path $repoRoot "infra\litellm\stop-litellm.ps1"
$studioStop = Join-Path $repoRoot "infra\agent1\stop-studio.ps1"
$langflowStop = Join-Path $repoRoot "infra\agent1\stop-langflow.ps1"
$lokiStop = Join-Path $repoRoot "infra\loki\stop-loki.ps1"
$promStop = Join-Path $repoRoot "infra\prometheus\stop-prometheus.ps1"
$alloyStop = Join-Path $repoRoot "infra\alloy\stop-alloy.ps1"
$grafanaStop = Join-Path $repoRoot "infra\grafana\stop-grafana.ps1"
$metabaseStop = Join-Path $repoRoot "infra\metabase\stop-metabase.ps1"
$n8nStop = Join-Path $repoRoot "infra\n8n\stop-n8n.ps1"
$difyStop = Join-Path $repoRoot "infra\dify\stop-dify.ps1"

function Stop-PortListeners {
    param([int]$Port, [string]$Label)
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    if (-not $listeners) {
        Write-Host "$Label is not running on :$Port"
        return
    }
    foreach ($procId in $listeners) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped $Label on :$Port (PID $procId)"
    }
}

Write-Host "=== alexsoft local stack: stop ===" -ForegroundColor Cyan

if (-not $SkipAi) {
    if (Test-Path $langflowStop) {
        Write-Host "[..] Stopping LangFlow..."
        & powershell -ExecutionPolicy Bypass -File $langflowStop
    }
    if (Test-Path $studioStop) {
        Write-Host "[..] Stopping Studio..."
        & powershell -ExecutionPolicy Bypass -File $studioStop
    }
    if (Test-Path $litellmStop) {
        Write-Host "[..] Stopping LiteLLM..."
        & powershell -ExecutionPolicy Bypass -File $litellmStop
    }
}
else {
    Write-Host "[--] AI left running (-SkipAi)" -ForegroundColor DarkYellow
}

if (-not $SkipData) {
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
}
else {
    Write-Host "[--] Data left running (-SkipData)" -ForegroundColor DarkYellow
}

if ($WithObs) {
    if (Test-Path $alloyStop) { & powershell -ExecutionPolicy Bypass -File $alloyStop }
    if (Test-Path $grafanaStop) { & powershell -ExecutionPolicy Bypass -File $grafanaStop }
    if (Test-Path $promStop) { & powershell -ExecutionPolicy Bypass -File $promStop }
    if (Test-Path $lokiStop) { & powershell -ExecutionPolicy Bypass -File $lokiStop }
}

if ($WithBi) {
    if (Test-Path $metabaseStop) { & powershell -ExecutionPolicy Bypass -File $metabaseStop }
}

if ($WithN8n) {
    if (Test-Path $n8nStop) {
        Write-Host "[..] Stopping n8n..."
        & powershell -ExecutionPolicy Bypass -File $n8nStop
    }
}

if ($WithDify) {
    if (Test-Path $difyStop) {
        Write-Host "[..] Stopping Dify..."
        & powershell -ExecutionPolicy Bypass -File $difyStop
    }
}

if ($WithLanding) {
    Write-Host "[..] Stopping Landing (:3000)..."
    Stop-PortListeners -Port 3000 -Label "Landing"
}

if ($WithGames) {
    Write-Host "[..] Stopping Games (:3010)..."
    Stop-PortListeners -Port 3010 -Label "Games"
}

Write-Host "=== done ===" -ForegroundColor Cyan
Write-Host "PostgreSQL Windows service left running (stop via services.msc if needed)."

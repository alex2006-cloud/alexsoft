# Start alexsoft local services (native Windows).
# Default: data (Postgres/Memurai/MinIO) + AI (LiteLLM, Studio, LangFlow).
# Optional: observability, Metabase, Landing, Games.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1 -WithLanding -WithGames
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1 -WithObs -WithBi
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1 -WithN8n -WithDify
#   powershell -ExecutionPolicy Bypass -File C:\alexsoft\scripts\dev-up.ps1 -SkipAi
#
# Stop: scripts\dev-down.ps1

param(
    [switch]$SkipAi,
    [switch]$SkipLangFlow,
    [switch]$SkipData,
    [switch]$WithLanding,
    [switch]$WithGames,
    [switch]$WithObs,
    [switch]$WithBi,
    [switch]$WithN8n,
    [switch]$WithDify
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$memuraiStart = Join-Path $env:LOCALAPPDATA "Memurai\start-memurai.ps1"
$minioStart = Join-Path $repoRoot "infra\minio\start-minio.ps1"
$litellmStart = Join-Path $repoRoot "infra\litellm\start-litellm.ps1"
$studioStart = Join-Path $repoRoot "infra\agent1\start-studio.ps1"
$langflowStart = Join-Path $repoRoot "infra\agent1\start-langflow.ps1"
$lokiStart = Join-Path $repoRoot "infra\loki\start-loki.ps1"
$promStart = Join-Path $repoRoot "infra\prometheus\start-prometheus.ps1"
$alloyStart = Join-Path $repoRoot "infra\alloy\start-alloy.ps1"
$grafanaStart = Join-Path $repoRoot "infra\grafana\start-grafana.ps1"
$metabaseStart = Join-Path $repoRoot "infra\metabase\start-metabase.ps1"
$n8nStart = Join-Path $repoRoot "infra\n8n\start-n8n.ps1"
$difyStart = Join-Path $repoRoot "infra\dify\start-dify.ps1"

function Test-PortListen {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Invoke-StartScript {
    param(
        [string]$Label,
        [string]$ScriptPath,
        [int]$ReadyPort = 0,
        [int]$WaitSeconds = 0,
        [switch]$Optional
    )
    Write-Host ""
    Write-Host ("... {0}" -f $Label) -ForegroundColor Yellow
    if (-not (Test-Path $ScriptPath)) {
        if ($Optional) {
            Write-Host ("WARN start script missing (optional): {0}" -f $ScriptPath) -ForegroundColor DarkYellow
            return
        }
        Write-Error "Start script not found: $ScriptPath"
    }
    if ($ReadyPort -gt 0 -and (Test-PortListen -Port $ReadyPort)) {
        Write-Host ("OK  already listening on :{0} - skip" -f $ReadyPort) -ForegroundColor Green
        return
    }
    try {
        & powershell -ExecutionPolicy Bypass -File $ScriptPath
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            throw ("{0} failed (exit {1}): {2}" -f $Label, $LASTEXITCODE, $ScriptPath)
        }
        if ($WaitSeconds -gt 0) { Start-Sleep -Seconds $WaitSeconds }
        if ($ReadyPort -gt 0) {
            $deadline = (Get-Date).AddSeconds(30)
            while ((Get-Date) -lt $deadline) {
                if (Test-PortListen -Port $ReadyPort) { break }
                Start-Sleep -Seconds 1
            }
            if (-not (Test-PortListen -Port $ReadyPort)) {
                throw ("{0} did not open port {1}" -f $Label, $ReadyPort)
            }
        }
        Write-Host ("OK  {0} up" -f $Label) -ForegroundColor Green
    }
    catch {
        if ($Optional) {
            Write-Host ("WARN {0} failed (optional, continuing): {1}" -f $Label, $_.Exception.Message) -ForegroundColor DarkYellow
            return
        }
        throw
    }
}

Write-Host "=== alexsoft local stack ===" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot"
Write-Host ""

# --- PostgreSQL ---
$pg = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($pg) {
    if ($pg.Status -eq "Running") {
        Write-Host "OK  PostgreSQL service already running (port 5432)" -ForegroundColor Green
    }
    else {
        Write-Host "... Starting PostgreSQL service..." -ForegroundColor Yellow
        Start-Service -Name "postgresql-x64-16"
        Start-Sleep -Seconds 2
        Write-Host "OK  PostgreSQL started" -ForegroundColor Green
    }
}
else {
    Write-Host "--  PostgreSQL service postgresql-x64-16 not found (skip)" -ForegroundColor DarkYellow
}

if (-not $SkipData) {
    # --- Memurai (Redis) ---
    if (-not (Test-Path $memuraiStart)) {
        Write-Host ""
        Write-Host "--  Memurai start script missing - skip Redis (:6379)" -ForegroundColor DarkYellow
        Write-Host "    See infra/redis/README.md" -ForegroundColor DarkYellow
    }
    elseif (Test-PortListen -Port 6379) {
        Write-Host ""
        Write-Host "OK  Memurai already listening on 6379" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "... Memurai (Redis :6379)..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $memuraiStart
        if (-not (Test-PortListen -Port 6379)) {
            Write-Error "Memurai did not open port 6379"
        }
        Write-Host "OK  Memurai up" -ForegroundColor Green
    }

    # --- MinIO ---
    Invoke-StartScript -Label "MinIO (S3 :9000, Console :9001)" -ScriptPath $minioStart -ReadyPort 9000
}
else {
    Write-Host ""
    Write-Host "--  Data stack skipped (-SkipData)" -ForegroundColor DarkYellow
}

if (-not $SkipAi) {
    Invoke-StartScript -Label "LiteLLM (:8080)" -ScriptPath $litellmStart -ReadyPort 8080
    Invoke-StartScript -Label "LangSmith Studio / Agent Server (:2024)" -ScriptPath $studioStart -ReadyPort 2024
    if (-not $SkipLangFlow) {
        # Optional: LangFlow often breaks under system SOCKS proxies on Windows.
        Invoke-StartScript -Label "LangFlow (:7860)" -ScriptPath $langflowStart -ReadyPort 7860 -Optional
    }
    else {
        Write-Host ""
        Write-Host "--  LangFlow skipped (-SkipLangFlow)" -ForegroundColor DarkYellow
    }
}
else {
    Write-Host ""
    Write-Host "--  AI stack skipped (-SkipAi)" -ForegroundColor DarkYellow
}

if ($WithObs) {
    Invoke-StartScript -Label "Loki (:3100)" -ScriptPath $lokiStart -ReadyPort 3100
    Invoke-StartScript -Label "Prometheus (:9090)" -ScriptPath $promStart -ReadyPort 9090
    Invoke-StartScript -Label "Alloy (:12345)" -ScriptPath $alloyStart -ReadyPort 12345
    Invoke-StartScript -Label "Grafana (:3001)" -ScriptPath $grafanaStart -ReadyPort 3001
}
else {
    Write-Host ""
    Write-Host "--  Observability skipped (pass -WithObs)" -ForegroundColor DarkYellow
}

if ($WithBi) {
    Invoke-StartScript -Label "Metabase (:3002)" -ScriptPath $metabaseStart -ReadyPort 3002
}
else {
    Write-Host ""
    Write-Host "--  Metabase skipped (pass -WithBi)" -ForegroundColor DarkYellow
}

if ($WithN8n) {
    Invoke-StartScript -Label "n8n (:5678)" -ScriptPath $n8nStart -ReadyPort 5678 -Optional
}
else {
    Write-Host ""
    Write-Host "--  n8n skipped (pass -WithN8n)" -ForegroundColor DarkYellow
}

if ($WithDify) {
    # Docker Compose; first start may take minutes (image pull).
    Invoke-StartScript -Label "Dify (:3003)" -ScriptPath $difyStart -ReadyPort 3003 -Optional
}
else {
    Write-Host ""
    Write-Host "--  Dify skipped (pass -WithDify)" -ForegroundColor DarkYellow
}

if ($WithLanding) {
    Write-Host ""
    Write-Host "... Landing (next dev :3000)..." -ForegroundColor Yellow
    $landingDir = Join-Path $repoRoot "apps\landing"
    if (-not (Test-Path (Join-Path $landingDir "package.json"))) {
        Write-Error "Landing app not found: $landingDir"
    }
    if (Test-PortListen -Port 3000) {
        Write-Host "OK  Something already listens on 3000 - skip npm run dev" -ForegroundColor Green
    }
    else {
        $cmd = "Set-Location -LiteralPath '$landingDir'; npm run dev"
        Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command", $cmd
        )
        Write-Host "OK  Landing started in a new terminal window" -ForegroundColor Green
    }
}
else {
    Write-Host ""
    Write-Host "--  Landing skipped (pass -WithLanding)" -ForegroundColor DarkYellow
}

if ($WithGames) {
    Write-Host ""
    Write-Host "... Games (next dev :3010/games)..." -ForegroundColor Yellow
    $gamesDir = Join-Path $repoRoot "apps\games"
    if (-not (Test-Path (Join-Path $gamesDir "package.json"))) {
        Write-Error "Games app not found: $gamesDir"
    }
    if (Test-PortListen -Port 3010) {
        Write-Host "OK  Something already listens on 3010 - skip npm run dev" -ForegroundColor Green
    }
    else {
        $cmd = "Set-Location -LiteralPath '$gamesDir'; npm run dev"
        Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command", $cmd
        )
        Write-Host "OK  Games started in a new terminal window" -ForegroundColor Green
    }
}
else {
    Write-Host ""
    Write-Host "--  Games skipped (pass -WithGames)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== ready ===" -ForegroundColor Cyan
Write-Host "Postgres: 127.0.0.1:5432"
if (-not $SkipData) {
    Write-Host "Redis:    127.0.0.1:6379"
    Write-Host "MinIO:    http://127.0.0.1:9000"
    Write-Host "Console:  http://127.0.0.1:9001"
}
if (-not $SkipAi) {
    Write-Host "LiteLLM:  http://127.0.0.1:8080"
    Write-Host "Studio:   http://127.0.0.1:2024  (UI: smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)"
    if (-not $SkipLangFlow) {
        Write-Host "LangFlow: http://127.0.0.1:7860"
    }
}
if ($WithObs) {
    Write-Host "Loki:     http://127.0.0.1:3100"
    Write-Host "Prom:     http://127.0.0.1:9090"
    Write-Host "Grafana:  http://127.0.0.1:3001"
}
if ($WithBi) {
    Write-Host "Metabase: http://127.0.0.1:3002"
}
if ($WithN8n) {
    Write-Host "n8n:      http://127.0.0.1:5678"
}
if ($WithDify) {
    Write-Host "Dify:     http://127.0.0.1:3003"
}
if ($WithLanding) {
    Write-Host "Landing:  http://127.0.0.1:3000"
}
if ($WithGames) {
    Write-Host "Games:    http://127.0.0.1:3010/games"
}
Write-Host ""
$downScript = Join-Path $PSScriptRoot "dev-down.ps1"
Write-Host ("Stop with: powershell -ExecutionPolicy Bypass -File " + $downScript)

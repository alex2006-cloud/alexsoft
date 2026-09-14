# Start local Grafana Alloy (HTTP UI, default :12345). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\alloy\start-alloy.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$configSrc = Join-Path $scriptDir "config.alloy"
$alloyHome = Join-Path $env:LOCALAPPDATA "Alloy"
$alloyExe = Join-Path $alloyHome "alloy.exe"
$dataDir = Join-Path $alloyHome "data"
$demoDir = Join-Path $alloyHome "demo"
$demoLog = Join-Path $demoDir "app.log"
$logFile = Join-Path $alloyHome "alloy.log"
$errFile = Join-Path $alloyHome "alloy.err.log"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key=(.*)$") {
            return $Matches[1].Trim()
        }
    }
    return $Default
}

if (-not (Test-Path $alloyExe)) {
    Write-Error "alloy.exe not found at $alloyExe. Run install-alloy.ps1 first."
}
if (-not (Test-Path $configSrc)) {
    Write-Error "Config not found: $configSrc"
}

$port = Read-DotEnvValue -Path $envFile -Key "ALLOY_HTTP_PORT" -Default "12345"
$lokiPort = Read-DotEnvValue -Path $envFile -Key "LOKI_PORT" -Default "3100"
$promPort = Read-DotEnvValue -Path $envFile -Key "PROMETHEUS_PORT" -Default "9090"
$pgLogGlob = Read-DotEnvValue -Path $envFile -Key "POSTGRES_LOG_GLOB" -Default ""

if (-not $pgLogGlob) {
    foreach ($ver in @("16", "17", "15", "14")) {
        $checkDir = "C:\Program Files\PostgreSQL\$ver\data\log"
        if (-not (Test-Path $checkDir)) { continue }
        $day = Get-Date -Format "yyyy-MM-dd"
        $today = Get-ChildItem -Path $checkDir -Filter "postgresql-$day*.log" -ErrorAction SilentlyContinue
        if ($today) {
            $pgLogGlob = "C:/Program Files/PostgreSQL/$ver/data/log/postgresql-$day*.log"
        } else {
            $pgLogGlob = "C:/Program Files/PostgreSQL/$ver/data/log/postgresql-*.log"
        }
        break
    }
}
if (-not $pgLogGlob) {
    $day = Get-Date -Format "yyyy-MM-dd"
    $pgLogGlob = "C:/Program Files/PostgreSQL/16/data/log/postgresql-$day*.log"
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path $demoDir | Out-Null
if (-not (Test-Path $demoLog)) {
    [System.IO.File]::WriteAllText($demoLog, "")
}

# Forward slashes for Alloy/sys.env file paths on Windows
$demoLogEnv = ($demoLog -replace "\\", "/")

$env:ALLOY_HTTP_PORT = $port
$env:ALLOY_DEMO_LOG = $demoLogEnv
$env:POSTGRES_LOG_GLOB = ($pgLogGlob -replace "\\", "/")
$env:LOKI_PUSH_URL = "http://127.0.0.1:$lokiPort/loki/api/v1/push"
$env:PROMETHEUS_REMOTE_WRITE_URL = "http://127.0.0.1:$promPort/api/v1/write"

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Alloy already listening on 127.0.0.1:$port (PID $($listen.OwningProcess))"
    Write-Host "UI:      http://127.0.0.1:$port"
    Write-Host "Ready:   http://127.0.0.1:$port/-/ready"
    Write-Host "Demo log: $demoLog"
    Write-Host "PG logs:  $env:POSTGRES_LOG_GLOB"
    Write-Host "To apply config/env changes: stop-alloy.ps1 then start-alloy.ps1"
    exit 0
}

$args = @(
    "run",
    $configSrc,
    "--storage.path=$dataDir",
    "--server.http.listen-addr=127.0.0.1:$port",
    "--disable-reporting"
)

$proc = Start-Process -FilePath $alloyExe -ArgumentList $args -WorkingDirectory $alloyHome `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(45)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if (-not $up) { continue }
    try {
        $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 2 "http://127.0.0.1:$port/-/ready"
        if ($code -eq "200") {
            $ready = $true
            break
        }
    } catch {
        # warming up
    }
}

if (-not $ready) {
    Write-Error "Alloy did not become ready on port $port. See $logFile and $errFile"
}

Write-Host "Alloy started (PID $($proc.Id))"
Write-Host "UI:       http://127.0.0.1:$port"
Write-Host "Ready:    http://127.0.0.1:$port/-/ready"
Write-Host "Metrics:  http://127.0.0.1:$port/metrics"
Write-Host "Demo log: $demoLog"
Write-Host "PG logs:  $env:POSTGRES_LOG_GLOB"
Write-Host "Loki push: $env:LOKI_PUSH_URL"
Write-Host "Prom RW:   $env:PROMETHEUS_REMOTE_WRITE_URL"
Write-Host "Data:     $dataDir"
Write-Host "Config:   $configSrc"
Write-Host "Log:      $logFile"

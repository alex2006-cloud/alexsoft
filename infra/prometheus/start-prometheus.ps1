# Start local Prometheus (HTTP UI/API, default :9090). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$configSrc = Join-Path $scriptDir "prometheus.yml"
$promHome = Join-Path $env:LOCALAPPDATA "Prometheus"
$promExe = Join-Path $promHome "prometheus.exe"
$dataDir = Join-Path $promHome "data"
$logFile = Join-Path $promHome "prometheus.log"
$errFile = Join-Path $promHome "prometheus.err.log"

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

if (-not (Test-Path $promExe)) {
    Write-Error "prometheus.exe not found at $promExe. Run install-prometheus.ps1 first."
}
if (-not (Test-Path $configSrc)) {
    Write-Error "Config not found: $configSrc"
}

$port = Read-DotEnvValue -Path $envFile -Key "PROMETHEUS_PORT" -Default "9090"

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Prometheus already listening on 127.0.0.1:$port (PID $($listen.OwningProcess))"
    Write-Host "UI:    http://127.0.0.1:$port"
    Write-Host "Ready: http://127.0.0.1:$port/-/ready"
    exit 0
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

$args = @(
    "--config.file=$configSrc",
    "--storage.tsdb.path=$dataDir",
    "--web.listen-address=127.0.0.1:$port",
    "--web.enable-lifecycle",
    # Accept metrics pushed by Alloy (prometheus.remote_write)
    "--web.enable-remote-write-receiver"
)

$proc = Start-Process -FilePath $promExe -ArgumentList $args -WorkingDirectory $promHome `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(30)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if (-not $up) { continue }
    try {
        $body = & curl.exe -s --max-time 2 "http://127.0.0.1:$port/-/ready"
        if ($body -match "Prometheus Server is Ready") {
            $ready = $true
            break
        }
    } catch {
        # warming up
    }
}

if (-not $ready) {
    Write-Error "Prometheus did not become ready on port $port. See $logFile and $errFile"
}

Write-Host "Prometheus started (PID $($proc.Id))"
Write-Host "UI:       http://127.0.0.1:$port"
Write-Host "Ready:    http://127.0.0.1:$port/-/ready"
Write-Host "Metrics:  http://127.0.0.1:$port/metrics"
Write-Host "Targets:  http://127.0.0.1:$port/targets"
Write-Host "Data:     $dataDir"
Write-Host "Log:      $logFile"

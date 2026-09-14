# Start local Loki (HTTP API, default :3100). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$configSrc = Join-Path $scriptDir "loki-local-config.yaml"
$lokiHome = Join-Path $env:LOCALAPPDATA "Loki"
$lokiExe = Join-Path $lokiHome "loki.exe"
$dataDir = Join-Path $lokiHome "data"
$logFile = Join-Path $lokiHome "loki.log"
$errFile = Join-Path $lokiHome "loki.err.log"

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

if (-not (Test-Path $lokiExe)) {
    Write-Error "loki.exe not found at $lokiExe. Run install-loki.ps1 first."
}
if (-not (Test-Path $configSrc)) {
    Write-Error "Config not found: $configSrc"
}

$port = Read-DotEnvValue -Path $envFile -Key "LOKI_PORT" -Default "3100"
$grpcPort = Read-DotEnvValue -Path $envFile -Key "LOKI_GRPC_PORT" -Default "9096"

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Loki already listening on 127.0.0.1:$port (PID $($listen.OwningProcess))"
    Write-Host "Ready: http://127.0.0.1:$port/ready"
    exit 0
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "chunks") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "rules") | Out-Null

# Loki expand-env expects forward slashes on Windows paths in YAML.
$dataDirEnv = ($dataDir -replace "\\", "/")

$env:LOKI_PORT = $port
$env:LOKI_GRPC_PORT = $grpcPort
$env:LOKI_DATA = $dataDirEnv

$args = @(
    "--config.file=$configSrc",
    "--config.expand-env=true"
)

$proc = Start-Process -FilePath $lokiExe -ArgumentList $args -WorkingDirectory $lokiHome `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(45)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if (-not $up) { continue }
    try {
        $body = & curl.exe -s --max-time 2 "http://127.0.0.1:$port/ready"
        if ($body -eq "ready") {
            $ready = $true
            break
        }
    } catch {
        # still warming up (ingester delay)
    }
}

if (-not $ready) {
    Write-Error "Loki did not become ready on port $port. See $logFile and $errFile"
}

Write-Host "Loki started (PID $($proc.Id))"
Write-Host "HTTP API: http://127.0.0.1:$port"
Write-Host "Ready:    http://127.0.0.1:$port/ready"
Write-Host "gRPC:     127.0.0.1:$grpcPort"
Write-Host "Data:     $dataDir"
Write-Host "Log:      $logFile"

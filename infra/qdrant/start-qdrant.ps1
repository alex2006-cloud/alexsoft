# Start local Qdrant (REST :6333, gRPC :6334). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\qdrant\start-qdrant.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$qdrantHome = Join-Path $env:LOCALAPPDATA "Qdrant"
$qdrantExe = Join-Path $qdrantHome "qdrant.exe"
$dataDir = Join-Path $qdrantHome "storage"
$snapDir = Join-Path $qdrantHome "snapshots"
$logFile = Join-Path $qdrantHome "qdrant.log"
$errFile = Join-Path $qdrantHome "qdrant.err.log"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

if (-not (Test-Path $qdrantExe)) {
    Write-Error "qdrant.exe not found at $qdrantExe. Run install-qdrant.ps1 first."
}

$httpPort = [int](Read-DotEnvValue -Path $envFile -Key "QDRANT_HTTP_PORT" -Default "6333")
$grpcPort = [int](Read-DotEnvValue -Path $envFile -Key "QDRANT_GRPC_PORT" -Default "6334")
$apiKey = Read-DotEnvValue -Path $envFile -Key "QDRANT_API_KEY" -Default ""

$listen = Get-NetTCPConnection -LocalPort $httpPort -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Qdrant already listening on 127.0.0.1:$httpPort (PID $($listen[0].OwningProcess))"
    exit 0
}

New-Item -ItemType Directory -Force -Path $dataDir, $snapDir | Out-Null

$env:QDRANT__SERVICE__HOST = "127.0.0.1"
$env:QDRANT__SERVICE__HTTP_PORT = "$httpPort"
$env:QDRANT__SERVICE__GRPC_PORT = "$grpcPort"
$env:QDRANT__STORAGE__STORAGE_PATH = $dataDir
$env:QDRANT__STORAGE__SNAPSHOTS_PATH = $snapDir
$env:QDRANT__TELEMETRY_DISABLED = "true"
if ($apiKey) { $env:QDRANT__SERVICE__API_KEY = $apiKey }

$proc = Start-Process -FilePath $qdrantExe -WorkingDirectory $qdrantHome `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(20)
$up = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    $up = Get-NetTCPConnection -LocalPort $httpPort -State Listen -ErrorAction SilentlyContinue
    if ($up) { break }
}
if (-not $up) {
    Write-Error "Qdrant did not start. See $errFile / $logFile"
}

Write-Host "Qdrant started (PID $($proc.Id))"
Write-Host "REST:      http://127.0.0.1:$httpPort  (dashboard: /dashboard)"
Write-Host "gRPC:      127.0.0.1:$grpcPort"
Write-Host "Storage:   $dataDir"
Write-Host "Log:       $errFile"

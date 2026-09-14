# Stop local Loki started by start-loki.ps1.
# powershell -ExecutionPolicy Bypass -File infra\loki\stop-loki.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"

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

$port = [int](Read-DotEnvValue -Path $envFile -Key "LOKI_PORT" -Default "3100")
$grpcPort = [int](Read-DotEnvValue -Path $envFile -Key "LOKI_GRPC_PORT" -Default "9096")

$listeners = Get-NetTCPConnection -LocalPort $port, $grpcPort -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $listeners) {
    $byName = Get-Process -Name loki -ErrorAction SilentlyContinue
    if (-not $byName) {
        Write-Host "Loki is not running."
        exit 0
    }
    $listeners = $byName.Id
}

foreach ($procId in $listeners) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $procId"
}

Start-Sleep -Milliseconds 500
Write-Host "Loki stopped."

# Stop local Grafana started by start-grafana.ps1.
# powershell -ExecutionPolicy Bypass -File infra\grafana\stop-grafana.ps1

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

$port = [int](Read-DotEnvValue -Path $envFile -Key "GRAFANA_PORT" -Default "3001")

$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $listeners) {
    $byName = @()
    $byName += Get-Process -Name grafana -ErrorAction SilentlyContinue
    $byName += Get-Process -Name grafana-server -ErrorAction SilentlyContinue
    if (-not $byName) {
        Write-Host "Grafana is not running."
        exit 0
    }
    $listeners = $byName.Id
}

foreach ($procId in $listeners) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $procId"
}

Start-Sleep -Milliseconds 500
Write-Host "Grafana stopped."

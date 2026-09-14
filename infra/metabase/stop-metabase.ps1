# Stop local Metabase started by start-metabase.ps1.
# powershell -ExecutionPolicy Bypass -File infra\metabase\stop-metabase.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$metabaseHome = Join-Path $env:LOCALAPPDATA "Metabase"
$pidFile = Join-Path $metabaseHome "metabase.pid"

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

$port = [int](Read-DotEnvValue -Path $envFile -Key "METABASE_PORT" -Default "3002")
$toStop = @()

$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
if ($listeners) { $toStop += $listeners }

if (Test-Path $pidFile) {
    $saved = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($saved -match '^\d+$') { $toStop += [int]$saved }
}

$toStop = $toStop | Select-Object -Unique
if (-not $toStop) {
    Write-Host "Metabase is not running."
    exit 0
}

foreach ($procId in $toStop) {
    $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if (-not $p) { continue }
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $procId ($($p.ProcessName))"
}

if (Test-Path $pidFile) { Remove-Item -Force $pidFile }
Start-Sleep -Milliseconds 500
Write-Host "Metabase stopped."

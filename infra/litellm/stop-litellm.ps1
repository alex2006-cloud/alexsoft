# Stop local LiteLLM started by start-litellm.ps1.
# powershell -ExecutionPolicy Bypass -File infra\litellm\stop-litellm.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$litellmHome = Join-Path $env:LOCALAPPDATA "LiteLLM"
$pidFile = Join-Path $litellmHome "litellm.pid"

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

$port = [int](Read-DotEnvValue -Path $envFile -Key "LITELLM_PORT" -Default "8080")
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
    Write-Host "LiteLLM is not running."
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
Write-Host "LiteLLM stopped."

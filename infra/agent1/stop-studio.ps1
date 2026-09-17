# Stop LangGraph Agent Server started by start-studio.ps1
# powershell -ExecutionPolicy Bypass -File infra\agent1\stop-studio.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$pidFile = Join-Path $script:Agent1Home "studio.pid"
$port = 2024
if ($env:AGENT1_STUDIO_PORT) { $port = [int]$env:AGENT1_STUDIO_PORT }

if (Test-Path $pidFile) {
    $procId = [int](Get-Content $pidFile -Raw).Trim()
    if ($procId -gt 0) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped PID $procId"
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped process on port $port (PID $($_.OwningProcess))"
    }

Write-Host "Studio stopped."

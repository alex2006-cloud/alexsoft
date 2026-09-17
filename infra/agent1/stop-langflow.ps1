# Stop LangFlow started by start-langflow.ps1
# powershell -ExecutionPolicy Bypass -File infra\agent1\stop-langflow.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$pidFile = Join-Path $script:LangFlowHome "langflow.pid"
$port = 7860
if ($env:LANGFLOW_PORT) { $port = [int]$env:LANGFLOW_PORT }

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

Write-Host "LangFlow stopped."

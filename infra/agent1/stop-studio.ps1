# Stop LangGraph Agent Server started by start-studio.ps1
# powershell -ExecutionPolicy Bypass -File infra\agent1\stop-studio.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$port = 2024
if ($env:AGENT1_STUDIO_PORT) { $port = [int]$env:AGENT1_STUDIO_PORT }

if (Stop-Agent1Studio -Port $port) {
    Write-Host "Studio stopped."
} else {
    Write-Warning "Port $port is still serving after cleanup - a non-Agent1 process may hold it."
}

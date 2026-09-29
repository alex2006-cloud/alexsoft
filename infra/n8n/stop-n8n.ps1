# Stop n8n started by start-n8n.ps1
# powershell -ExecutionPolicy Bypass -File infra\n8n\stop-n8n.ps1

$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "common.ps1")

Import-N8nEnv
$port = [int]$env:N8N_PORT

if (Test-Path $script:N8nPidFile) {
    $procId = Get-Content $script:N8nPidFile -ErrorAction SilentlyContinue
    if ($procId) {
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped n8n PID $procId"
    }
    Remove-Item $script:N8nPidFile -Force -ErrorAction SilentlyContinue
}

Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped listener on :$port (PID $_)"
    }

Write-Host "n8n stop done"

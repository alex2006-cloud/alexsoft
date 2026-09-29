# Stop Dify Docker Compose stack.
# powershell -ExecutionPolicy Bypass -File infra\dify\stop-dify.ps1

$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "common.ps1")

Import-DifyEnv

if (-not (Test-Path $script:DifyDocker)) {
    Write-Host "Dify docker dir missing ($script:DifyDocker) - nothing to stop."
    exit 0
}

Write-Host "Stopping Dify (docker compose down) ..."
Push-Location $script:DifyDocker
try {
    & docker compose down
} finally {
    Pop-Location
}

Write-Host "Dify stop done"

# Stop Authentik containers (data and database are kept).
# powershell -ExecutionPolicy Bypass -File infra\authentik\stop-authentik.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-DockerReady)) { Write-Host "Docker is not running - nothing to stop."; exit 0 }
$envFile = New-ComposeEnvFile -Source (Join-Path (Get-RepoRoot) ".env")
Push-Location $PSScriptRoot
try { & docker compose --env-file $envFile -f compose.yml down }
finally { Pop-Location }
Write-Host "Authentik stopped."

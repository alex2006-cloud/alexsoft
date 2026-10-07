# Create venv and install apps/api (editable, with dev extras) into %LOCALAPPDATA%\AlexsoftApi\venv.
# powershell -ExecutionPolicy Bypass -File infra\api\install-api.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Ensure-ApiVenv
Ensure-PipReady

$appDir = Join-Path (Get-RepoRoot) "apps\api"
Write-Host "Installing $appDir ..."
& $script:ApiPython -m pip install -e "$appDir[dev]"
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed" }

& $script:ApiPython -c "import alexsoft_api, jwt, asyncpg, fastapi; print('alexsoft_api OK; fastapi', fastapi.__version__)"
Write-Host ""
Write-Host "Tests: infra\api\test-api.ps1   |   Run: infra\api\start-api.ps1"

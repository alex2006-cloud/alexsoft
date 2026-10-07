# Run apps/api unit tests (no Postgres / Authentik needed).
# powershell -ExecutionPolicy Bypass -File infra\api\test-api.ps1
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
if (-not (Test-Path $script:ApiPython)) { Write-Error "venv not found. Run install-api.ps1 first." }
Push-Location (Join-Path (Get-RepoRoot) "apps\api")
try { & $script:ApiPython -m pytest -q @args; exit $LASTEXITCODE }
finally { Pop-Location }

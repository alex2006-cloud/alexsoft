# Generate Prisma Python client for LiteLLM proxy (needed for Admin UI).
# Uses LITELLM_DATABASE_URL from repo .env. Run after install-litellm.ps1 + setup-db.ps1.
# powershell -ExecutionPolicy Bypass -File infra\litellm\setup-prisma.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$litellmHome = Join-Path $env:LOCALAPPDATA "LiteLLM"
$venvScripts = Join-Path $litellmHome "venv\Scripts"
$venvPython = Join-Path $venvScripts "python.exe"
$prismaExe = Join-Path $venvScripts "prisma.exe"
$schema = Join-Path $litellmHome "venv\Lib\site-packages\litellm\proxy\schema.prisma"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

if (-not (Test-Path $venvPython)) {
    Write-Error "LiteLLM venv missing. Run install-litellm.ps1 first."
}
if (-not (Test-Path $schema)) {
    Write-Error "schema.prisma not found at $schema"
}

$dbUrl = Read-DotEnvValue -Path $envFile -Key "LITELLM_DATABASE_URL" -Default ""
if (-not $dbUrl) {
    Write-Error "LITELLM_DATABASE_URL empty. Run setup-db.ps1 first."
}

$env:DATABASE_URL = $dbUrl
$env:Path = "$venvScripts;" + $env:Path

Write-Host "Fetching Prisma engines ..."
& $venvPython -m prisma py fetch
if ($LASTEXITCODE -ne 0) {
    Write-Warning "prisma py fetch returned $LASTEXITCODE"
}

Write-Host "Generating Prisma client ..."
Push-Location (Split-Path -Parent $schema)
try {
    & $prismaExe generate
    if ($LASTEXITCODE -ne 0) {
        Write-Error "prisma generate failed"
    }
} finally {
    Pop-Location
}

Write-Host "Pushing schema to database (baseline for empty litellm DB) ..."
& $prismaExe db push --schema $schema --skip-generate --accept-data-loss
if ($LASTEXITCODE -ne 0) {
    Write-Error "prisma db push failed"
}

Write-Host "Prisma ready. Next: start-litellm.ps1 (without LITELLM_SKIP_DB)"

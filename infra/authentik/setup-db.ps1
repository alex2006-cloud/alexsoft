# Create role + database "authentik" in the native PostgreSQL 16.
# Tries the app role from .env first; if it lacks CREATEROLE/CREATEDB, asks for the 'postgres' superuser password.
# powershell -ExecutionPolicy Bypass -File infra\authentik\setup-db.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$repo = Get-RepoRoot
$envFile = Join-Path $repo ".env"
$pgHost = Read-DotEnvValue -Path $envFile -Key "POSTGRES_HOST" -Default "127.0.0.1"
if ($pgHost -eq "localhost") { $pgHost = "127.0.0.1" }
$pgPort = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PORT" -Default "5432"
$appUser = Read-DotEnvValue -Path $envFile -Key "POSTGRES_USER" -Default "alexsoft"
$appPass = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PASSWORD" -Default ""
$dbName = Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_DB_NAME" -Default "authentik"
$dbUser = Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_DB_USER" -Default "authentik"
$dbPass = Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_DB_PASSWORD" -Default ""
if (-not $dbPass -or $dbPass -eq "change-me") { Write-Error "AUTHENTIK_DB_PASSWORD is not set. Run infra\authentik\init-env.ps1 first." }

$psql = Find-Psql
if (-not $psql) { Write-Error "psql.exe not found. Install PostgreSQL client tools (ADR-0004)." }
$sqlFile = Join-Path $PSScriptRoot "setup\01-create-authentik-db.sql"

function Invoke-Setup {
    param([string]$User, [string]$Password)
    if ($Password) { $env:PGPASSWORD = $Password } else { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $psql -h $pgHost -p $pgPort -U $User -d postgres -v ON_ERROR_STOP=1 `
        -v "u=$dbUser" -v "pw=$dbPass" -v "db=$dbName" -f $sqlFile 2>&1 | ForEach-Object { "$_" } | Out-Host
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    return $code
}

Write-Host "Trying as '$appUser' ..."
$code = Invoke-Setup -User $appUser -Password $appPass
if ($code -ne 0) {
    Write-Host ""
    Write-Host "'$appUser' cannot create roles/databases. Enter the 'postgres' superuser password when asked." -ForegroundColor Yellow
    $code = Invoke-Setup -User "postgres" -Password ""
}
if ($code -ne 0) { Write-Error "Could not create role/database for Authentik." }
Write-Host "OK  database '$dbName' (owner '$dbUser') is ready." -ForegroundColor Green
Write-Host "Next: infra\authentik\configure-postgres.ps1 (as Administrator), then start-authentik.ps1"

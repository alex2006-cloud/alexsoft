# Prepare Postgres for LiteLLM Admin UI (Prisma).
# Prefers DB `litellm`; if CREATE DATABASE is denied, uses schema `litellm` inside `alexsoft`.
# powershell -ExecutionPolicy Bypass -File infra\litellm\setup-db.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"

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

function Find-Psql {
    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    foreach ($c in @(
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    )) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

function Set-LitellmDatabaseUrl {
    param([string]$Url)
    $raw = Get-Content -Raw -Path $envFile
    if ($raw -match '(?m)^\s*#?\s*LITELLM_DATABASE_URL\s*=') {
        $updated = [regex]::Replace($raw, '(?m)^\s*#?\s*LITELLM_DATABASE_URL\s*=.*$', "LITELLM_DATABASE_URL=$Url")
        Set-Content -Path $envFile -Value $updated.TrimEnd() -Encoding utf8
        Write-Host "Updated LITELLM_DATABASE_URL in .env"
    } else {
        Add-Content -Path $envFile -Value "`nLITELLM_DATABASE_URL=$Url"
        Write-Host "Appended LITELLM_DATABASE_URL to .env"
    }
}

$hostName = Read-DotEnvValue -Path $envFile -Key "POSTGRES_HOST" -Default "localhost"
$port = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PORT" -Default "5432"
$user = Read-DotEnvValue -Path $envFile -Key "POSTGRES_USER" -Default "alexsoft"
$password = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PASSWORD" -Default ""
$appDb = Read-DotEnvValue -Path $envFile -Key "POSTGRES_DB" -Default "alexsoft"
$dbName = "litellm"

if (-not $password) {
    Write-Error "POSTGRES_PASSWORD is empty in .env"
}

$psql = Find-Psql
if (-not $psql) {
    Write-Error "psql.exe not found. Install PostgreSQL client tools (ADR-0004)."
}

$urlHost = if ($hostName -eq "localhost") { "127.0.0.1" } else { $hostName }
$encUser = [Uri]::EscapeDataString($user)
$encPass = [Uri]::EscapeDataString($password)
$env:PGPASSWORD = $password

$exists = & $psql -h $hostName -p $port -U $user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$dbName'" 2>$null
if ($LASTEXITCODE -ne 0) {
    # Some roles cannot connect to DB postgres; try app DB for existence check later.
    $exists = ""
}

$mode = $null
if ($exists -match "1") {
    $mode = "database"
    Write-Host "Database '$dbName' already exists."
} else {
    Write-Host "Trying CREATE DATABASE $dbName ..."
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $psql -h $hostName -p $port -U $user -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $dbName OWNER $user;" 2>&1 | Out-Null
    $createDbExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    if ($createDbExit -eq 0) {
        $mode = "database"
        Write-Host "Created database '$dbName'."
    } else {
        Write-Host "CREATE DATABASE denied for '$user'. Falling back to schema '$dbName' in database '$appDb'."
        & $psql -h $hostName -p $port -U $user -d $appDb -v ON_ERROR_STOP=1 -c "CREATE SCHEMA IF NOT EXISTS $dbName AUTHORIZATION $user;"
        if ($LASTEXITCODE -ne 0) {
            Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
            Write-Error "Could not create database or schema. Grant CREATEDB to $user as postgres, or create DB manually."
        }
        $mode = "schema"
        Write-Host "Created/ensured schema '$dbName' in '$appDb'."
    }
}

if ($mode -eq "database") {
    $litellmUrl = "postgresql://${encUser}:${encPass}@${urlHost}:${port}/${dbName}"
} else {
    $litellmUrl = "postgresql://${encUser}:${encPass}@${urlHost}:${port}/${appDb}?schema=${dbName}"
}

Set-LitellmDatabaseUrl -Url $litellmUrl
Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
Write-Host "Mode: $mode"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\litellm\start-litellm.ps1"

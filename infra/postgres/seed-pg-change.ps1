# Run a sample data-changing statement as alexsoft (needs log_statement=mod).
# Uses POSTGRES_* from repo .env (app role), not the postgres superuser.
# powershell -ExecutionPolicy Bypass -File infra\postgres\seed-pg-change.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key=(.*)$") {
            return $Matches[1].Trim()
        }
    }
    return $Default
}

if (-not (Test-Path $psql)) {
    Write-Error "psql not found at $psql"
}

$user = Read-DotEnvValue -Path $envFile -Key "POSTGRES_USER" -Default "alexsoft"
$db = Read-DotEnvValue -Path $envFile -Key "POSTGRES_DB" -Default "alexsoft"
$hostName = Read-DotEnvValue -Path $envFile -Key "POSTGRES_HOST" -Default "127.0.0.1"
$port = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PORT" -Default "5432"
$env:PGPASSWORD = Read-DotEnvValue -Path $envFile -Key "POSTGRES_PASSWORD" -Default ""

if (-not $env:PGPASSWORD) {
    Write-Error "POSTGRES_PASSWORD is empty in .env"
}

$sql = @"
CREATE TABLE IF NOT EXISTS observability_demo (
  id serial PRIMARY KEY,
  note text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO observability_demo (note) VALUES ('alloy-pg-log-check ' || to_char(now(), 'YYYY-MM-DD HH24:MI:SS'));
SELECT count(*) AS demo_rows FROM observability_demo;
"@

try {
    $sql | & $psql -h $hostName -p $port -U $user -d $db -v ON_ERROR_STOP=1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "psql failed with exit code $LASTEXITCODE"
    }
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Host "Inserted demo row. If log_statement=mod is on, Alloy should ship the SQL line to Loki (job=postgresql)."

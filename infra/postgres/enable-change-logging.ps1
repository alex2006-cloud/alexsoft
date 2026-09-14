# Enable PostgreSQL log_statement=mod (change logging) and reload config.
# Asks for the postgres superuser password (not read from .env).
# powershell -ExecutionPolicy Bypass -File infra\postgres\enable-change-logging.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sqlFile = Join-Path $scriptDir "enable-change-logging.sql"
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

if (-not (Test-Path $psql)) {
    Write-Error "psql not found at $psql. Adjust path for your PostgreSQL install."
}
if (-not (Test-Path $sqlFile)) {
    Write-Error "SQL not found: $sqlFile"
}

$secure = Read-Host -AsSecureString -Prompt "Password for PostgreSQL superuser 'postgres'"
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

try {
    & $psql -h 127.0.0.1 -U postgres -d postgres -v ON_ERROR_STOP=1 -f $sqlFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "psql failed with exit code $LASTEXITCODE"
    }
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Change logging enabled (log_statement=mod). Logs: C:\Program Files\PostgreSQL\16\data\log\"
Write-Host "Next: restart Alloy if needed, then run seed-pg-change.ps1 to generate a sample line."

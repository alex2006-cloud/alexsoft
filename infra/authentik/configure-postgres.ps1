# Let the Authentik container (Docker Desktop) reach the native PostgreSQL 16 on this machine:
#   1) pg_hba.conf: allow role/db "authentik" from private ranges (Docker Desktop / WSL2 networks)
#   2) Windows Firewall: inbound TCP 5432 from those ranges
#   3) reload PostgreSQL config
# Needs Administrator (the script re-launches itself elevated).
# powershell -ExecutionPolicy Bypass -File infra\authentik\configure-postgres.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Re-launching as Administrator (confirm UAC) ..."
    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -Wait -PassThru -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    exit $p.ExitCode
}

$envFile = Join-Path (Get-RepoRoot) ".env"
$dbName = Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_DB_NAME" -Default "authentik"
$dbUser = Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_DB_USER" -Default "authentik"
$pgPort = [int](Read-DotEnvValue -Path $envFile -Key "POSTGRES_PORT" -Default "5432")

$dataDir = "C:\Program Files\PostgreSQL\16\data"
$hba = Join-Path $dataDir "pg_hba.conf"
if (-not (Test-Path $hba)) { Write-Error "pg_hba.conf not found: $hba" }

$ranges = @("172.16.0.0/12", "192.168.0.0/16", "10.0.0.0/8")
$content = Get-Content -Raw $hba
$added = $false
foreach ($r in $ranges) {
    $line = "host    $dbName    $dbUser    $r    scram-sha-256"
    if ($content -notmatch [regex]::Escape("$dbName    $dbUser    $r")) {
        Add-Content -Path $hba -Value $line -Encoding ascii
        $added = $true
    }
}
if ($added) { Write-Host "pg_hba.conf: added rules for $dbUser@$dbName" } else { Write-Host "pg_hba.conf: rules already present" }

$ruleName = "alexsoft PostgreSQL for Docker (Authentik)"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $pgPort `
        -RemoteAddress $ranges -Profile Any | Out-Null
    Write-Host "Firewall: rule created"
} else {
    Write-Host "Firewall: rule already present"
}

$pgctl = "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe"
& $pgctl reload -D $dataDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "pg_ctl reload failed; restarting the PostgreSQL service instead ..." -ForegroundColor Yellow
    Restart-Service -Name "postgresql-x64-16"
}
Write-Host "OK  PostgreSQL config reloaded." -ForegroundColor Green
Start-Sleep -Seconds 2

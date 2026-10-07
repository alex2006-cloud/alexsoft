# Start Authentik (Docker Compose; DB in native Postgres). Starts Docker Desktop if needed.
# powershell -ExecutionPolicy Bypass -File infra\authentik\start-authentik.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$repo = Get-RepoRoot
$envFile = Join-Path $repo ".env"
$port = [int](Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_PORT_HTTP" -Default "9100")

foreach ($k in @("AUTHENTIK_SECRET_KEY", "AUTHENTIK_DB_PASSWORD", "OIDC_CLIENT_SECRET", "AUTHENTIK_BL_TOKEN")) {
    $v = Read-DotEnvValue -Path $envFile -Key $k -Default ""
    if (-not $v -or $v -eq "change-me") { Write-Error "$k is not set in .env. Run infra\authentik\init-env.ps1 first." }
}

Start-DockerDesktopIfNeeded
$composeEnv = New-ComposeEnvFile -Source $envFile

Push-Location $PSScriptRoot
try {
    & docker compose --env-file $composeEnv -f compose.yml up -d
    if ($LASTEXITCODE -ne 0) { Write-Error "docker compose up failed" }
}
finally { Pop-Location }

Write-Host "Waiting for Authentik on :$port (first start runs DB migrations, can take a few minutes) ..."
$deadline = (Get-Date).AddSeconds(420)
$ok = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 3 "http://127.0.0.1:$port/-/health/ready/"
    if ($code -eq "200" -or $code -eq "204") { $ok = $true; break }
}
if (-not $ok) {
    Write-Host "Last server logs:" -ForegroundColor Yellow
    & docker compose --env-file $composeEnv -f (Join-Path $PSScriptRoot "compose.yml") logs --tail 40 server
    Write-Error "Authentik did not become ready. Check DB access: infra\authentik\setup-db.ps1, configure-postgres.ps1."
}
Write-Host "OK  Authentik up: http://127.0.0.1:$port  (admin UI: /if/admin/, user akadmin)" -ForegroundColor Green

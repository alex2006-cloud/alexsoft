# Render the gateway config from .env and (re)start nginx on GATEWAY_PORT (default 8000).
#   -Static : serve built apps/landing/out and apps/games/out instead of proxying the dev servers
# powershell -ExecutionPolicy Bypass -File infra\nginx\local\start-nginx.ps1

param([switch]$Static)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:NginxExe)) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "install-nginx.ps1")
    if (-not (Test-Path $script:NginxExe)) { Write-Error "nginx is not installed" }
}

$repo = Get-RepoRoot
$envFile = Join-Path $repo ".env"
$port = Read-DotEnvValue -Path $envFile -Key "GATEWAY_PORT" -Default "8000"
$siteUrl = (Read-DotEnvValue -Path $envFile -Key "PUBLIC_SITE_URL" -Default "http://alexsoft.localhost:8000").TrimEnd("/")
$authUrl = (Read-DotEnvValue -Path $envFile -Key "AUTH_PUBLIC_URL" -Default "http://auth.alexsoft.localhost:8000").TrimEnd("/")
$siteHost = ([Uri]$siteUrl).Host
$authHost = ([Uri]$authUrl).Host

$values = @{
    GATEWAY_PORT   = $port
    PUBLIC_SITE_URL = $siteUrl
    SITE_HOST      = $siteHost
    AUTH_HOST      = $authHost
    CABINET_PORT   = (Read-DotEnvValue -Path $envFile -Key "CABINET_PORT" -Default "3020")
    AUTHENTIK_PORT = (Read-DotEnvValue -Path $envFile -Key "AUTHENTIK_PORT_HTTP" -Default "9100")
    LANDING_OUT    = (ConvertTo-NginxPath (Join-Path $repo "apps\landing\out"))
    GAMES_OUT      = (ConvertTo-NginxPath (Join-Path $repo "apps\games\out"))
}

if ($Static -and -not (Test-Path (Join-Path $repo "apps\landing\out\index.html"))) {
    Write-Error "apps\landing\out is missing. Build first: cd apps\landing; npm run build"
}

$confDir = Join-Path $script:NginxDir "conf"
$landingSrc = Join-Path $PSScriptRoot ($(if ($Static) { "landing-static.conf" } else { "landing-dev.conf" }))
Set-Content -Path (Join-Path $confDir "landing.conf") -Value (Expand-Template -Text (Get-Content -Raw $landingSrc) -Values $values) -Encoding ascii
$main = Expand-Template -Text (Get-Content -Raw (Join-Path $PSScriptRoot "alexsoft.local.conf")) -Values $values
$confFile = Join-Path $confDir "alexsoft.conf"
Set-Content -Path $confFile -Value $main -Encoding ascii

$prefix = ConvertTo-NginxPath ($script:NginxDir + "\")
& $script:NginxExe -p $prefix -c $confFile -t
if ($LASTEXITCODE -ne 0) { Write-Error "nginx config test failed" }

# restart if already running
& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-nginx.ps1") | Out-Null

$proc = Start-Process -FilePath $script:NginxExe -ArgumentList @("-p", $prefix, "-c", (ConvertTo-NginxPath $confFile)) `
    -WorkingDirectory $script:NginxDir -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(15)
$ok = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    if (Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue) { $ok = $true; break }
}
if (-not $ok) {
    Write-Host (Get-Content (Join-Path $script:NginxDir "logs\error.log") -Tail 20 -ErrorAction SilentlyContinue | Out-String)
    Write-Error "nginx did not open port $port. See $script:NginxDir\logs\error.log"
}
Write-Host "OK  gateway up on :$port ($(if ($Static) { 'static' } else { 'dev proxies' }))" -ForegroundColor Green
Write-Host "Site:  $siteUrl"
Write-Host "Auth:  $authUrl"
Write-Host "Logs:  $script:NginxDir\logs"

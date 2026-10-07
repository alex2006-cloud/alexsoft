# Start the BL API (FastAPI, apps/api) on BL_PORT (default 8100), localhost only.
# Needs PostgreSQL; JWT verification needs Authentik (JWKS) for real tokens.
# powershell -ExecutionPolicy Bypass -File infra\api\start-api.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$envFile = Join-Path (Get-RepoRoot) ".env"
$port = [int](Read-DotEnvValue -Path $envFile -Key "BL_PORT" -Default "8100")
$logFile = Join-Path $script:ApiHome "api.out.log"
$errFile = Join-Path $script:ApiHome "api.err.log"
$pidFile = Join-Path $script:ApiHome "api.pid"

if (-not (Test-Path $script:ApiPython)) { Write-Error "venv not found at $script:ApiVenv. Run install-api.ps1 first." }

$listen = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "BL API already listening on 127.0.0.1:$port (PID $($listen[0].OwningProcess)). Run stop-api.ps1 to restart."
    exit 0
}

$env:NO_PROXY = "127.0.0.1,localhost,*.localhost"
$proc = Start-Process -FilePath $script:ApiPython -ArgumentList @("-m", "alexsoft_api") `
    -WorkingDirectory (Join-Path (Get-RepoRoot) "apps\api") `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru
Set-Content -Path $pidFile -Value $proc.Id

$deadline = (Get-Date).AddSeconds(40)
$ok = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { break }
    $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 2 "http://127.0.0.1:$port/health/live"
    if ($code -eq "200") { $ok = $true; break }
}
if (-not $ok) {
    Write-Host (Get-Content $errFile -Tail 25 -ErrorAction SilentlyContinue | Out-String)
    Write-Error "BL API did not start. See $errFile"
}
Write-Host "BL API started (PID $($proc.Id))"
Write-Host "API:    http://127.0.0.1:$port   (docs: /docs)"
Write-Host "Ready:  curl.exe http://127.0.0.1:$port/health/ready"
Write-Host "Log:    $errFile"

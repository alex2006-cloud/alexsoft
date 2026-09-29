# Start Dify via Docker Compose (GUI on DIFY_WEB_PORT, default 3003).
# powershell -ExecutionPolicy Bypass -File infra\dify\start-dify.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Assert-DockerReady
Import-DifyEnv

if (-not (Test-Path (Get-DifyDockerEnvPath))) {
    Write-Error "Dify not prepared. Run install-dify.ps1 first."
}

$webPort = $env:DIFY_WEB_PORT
Set-DifyEnvKey -Path (Get-DifyDockerEnvPath) -Key "EXPOSE_NGINX_PORT" -Value $webPort

Write-Host "Starting Dify (docker compose up -d) in $script:DifyDocker ..."
Push-Location $script:DifyDocker
try {
    & docker compose up -d --remove-orphans
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "compose up failed; retrying after compose down --remove-orphans ..."
        & docker compose down --remove-orphans 2>$null
        & docker compose up -d --remove-orphans
        if ($LASTEXITCODE -ne 0) {
            Write-Error "docker compose up failed (exit $LASTEXITCODE)."
        }
    }
} finally {
    Pop-Location
}

$deadline = (Get-Date).AddSeconds(300)
$ok = $false
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$webPort/" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ok = $true; break }
    } catch { }
    Start-Sleep -Seconds 5
}

if (-not $ok) {
    Write-Warning "Dify did not answer on :$webPort within timeout - containers may still be pulling/starting."
    Write-Host "Check: docker compose -f $script:DifyDocker\docker-compose.yaml ps"
} else {
    Write-Host "Dify UI ready."
}

Write-Host "UI: http://127.0.0.1:$webPort"
Write-Host "LiteLLM provider: OpenAI-API-compatible -> http://host.docker.internal:8080/v1"

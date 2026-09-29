# Clone Dify + prepare Docker Compose .env (EXPOSE_NGINX_PORT = DIFY_WEB_PORT).
# Requires Docker Desktop. Does NOT start containers (use start-dify.ps1).
# powershell -ExecutionPolicy Bypass -File infra\dify\install-dify.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Assert-DockerReady
Import-DifyEnv

New-Item -ItemType Directory -Force -Path $script:DifyHome | Out-Null
Write-RepoRootMarker -HomeDir $script:DifyHome

$ref = $env:DIFY_GIT_REF
$webPort = $env:DIFY_WEB_PORT

if (-not (Test-Path (Join-Path $script:DifyRepo ".git"))) {
    Write-Host "Cloning langgenius/dify (ref $ref) -> $script:DifyRepo ..."
    New-Item -ItemType Directory -Force -Path $script:DifyHome | Out-Null
    if (Test-Path $script:DifyRepo) {
        Remove-Item -Recurse -Force $script:DifyRepo
    }
    & git clone --depth 1 --branch $ref https://github.com/langgenius/dify.git $script:DifyRepo
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tag $ref clone failed; trying default branch clone + checkout ..."
        & git clone --depth 1 https://github.com/langgenius/dify.git $script:DifyRepo
        if ($LASTEXITCODE -ne 0) {
            Write-Error "git clone dify failed."
        }
        Push-Location $script:DifyRepo
        try {
            & git fetch --depth 1 origin tag $ref
            & git checkout $ref
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Could not checkout $ref; using default branch tip."
            }
        } finally {
            Pop-Location
        }
    }
} else {
    Write-Host "Dify repo already present: $script:DifyRepo"
}

if (-not (Test-Path $script:DifyDocker)) {
    Write-Error "Expected docker folder missing: $script:DifyDocker"
}

$envExample = Join-Path $script:DifyDocker ".env.example"
$envPath = Get-DifyDockerEnvPath
if (-not (Test-Path $envPath)) {
    if (-not (Test-Path $envExample)) {
        Write-Error "Missing $envExample"
    }
    Copy-Item $envExample $envPath
    Write-Host "Created $envPath from .env.example"
}

# Map nginx to alexsoft port (landing owns 3000).
Set-DifyEnvKey -Path $envPath -Key "EXPOSE_NGINX_PORT" -Value $webPort
Set-DifyEnvKey -Path $envPath -Key "EXPOSE_NGINX_SSL_PORT" -Value "3443"
# Console/app URLs for browser on host
Set-DifyEnvKey -Path $envPath -Key "CONSOLE_API_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "CONSOLE_WEB_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "SERVICE_API_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "APP_API_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "APP_WEB_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "FILES_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "TRIGGER_URL" -Value "http://127.0.0.1:$webPort"
Set-DifyEnvKey -Path $envPath -Key "ENDPOINT_URL_TEMPLATE" -Value "http://127.0.0.1:$webPort/e/{hook_id}"
Set-DifyEnvKey -Path $envPath -Key "NEXT_PUBLIC_SOCKET_URL" -Value "ws://127.0.0.1:$webPort"

Write-Host ""
Write-Host "Dify install prepared."
Write-Host "Home:  $script:DifyHome"
Write-Host "Docker compose dir: $script:DifyDocker"
Write-Host "GUI port: $webPort"
Write-Host "Next: start-dify.ps1 -> http://127.0.0.1:$webPort"
Write-Host "LiteLLM from containers: http://host.docker.internal:8080/v1 (see README)"

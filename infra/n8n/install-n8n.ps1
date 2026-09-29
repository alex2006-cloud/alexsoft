# Install n8n into %LOCALAPPDATA%\AlexsoftN8n\prefix (native Windows, npm).
# powershell -ExecutionPolicy Bypass -File infra\n8n\install-n8n.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Assert-NodeForN8n
New-Item -ItemType Directory -Force -Path $script:N8nHome | Out-Null
New-Item -ItemType Directory -Force -Path $script:N8nPrefix | Out-Null
Write-RepoRootMarker -HomeDir $script:N8nHome

$pkgJson = Join-Path $script:N8nPrefix "package.json"
if (-not (Test-Path $pkgJson)) {
    Set-Content -Path $pkgJson -Value '{"name":"alexsoft-n8n","private":true}' -Encoding utf8
}

Write-Host "Installing n8n into $script:N8nPrefix ..."
Push-Location $script:N8nPrefix
try {
    & npm install n8n
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install n8n failed."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path $script:N8nCli)) {
    Write-Error "n8n CLI not found at $script:N8nCli after install."
}

$ver = & $script:N8nCli --version 2>$null
Write-Host ""
Write-Host "n8n OK (version $ver)"
Write-Host "prefix: $script:N8nPrefix"
Write-Host "Next: start-n8n.ps1 -> http://127.0.0.1:5678"
Write-Host "LiteLLM credential: OpenAI base URL http://127.0.0.1:8080/v1 (see README)"

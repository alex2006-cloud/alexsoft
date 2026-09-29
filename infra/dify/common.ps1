# Shared helpers for Dify (Docker Compose exception, ADR-0014).
# Dot-source from other scripts in this folder.

$script:DifyHome = Join-Path $env:LOCALAPPDATA "AlexsoftDify"
$script:DifyRepo = Join-Path $script:DifyHome "repo"
$script:DifyDocker = Join-Path $script:DifyRepo "docker"
# Pin a known release tag; override with DIFY_GIT_REF in .env
$script:DifyDefaultRef = "1.11.1"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-RepoRootMarker {
    param([string]$HomeDir)
    $repoRoot = Get-RepoRoot
    Set-Content -Path (Join-Path $HomeDir "repo-root.txt") -Value $repoRoot -Encoding utf8
}

function Assert-DockerReady {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Error @"
Docker not found. Dify requires Docker Desktop (Compose).
Install Docker Desktop for Windows, start it, then re-run.
See ADR-0014: Dify is the stage-5 Docker exception.
"@
    }
    & docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker daemon not running. Start Docker Desktop, wait until it is ready, then re-run."
    }
    & docker compose version 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "docker compose not available. Update Docker Desktop and re-run."
    }
    Write-Host "Docker OK"
}

function Import-DifyEnv {
    $repoRoot = Get-RepoRoot
    $envFile = Join-Path $repoRoot ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            $line = $_.Trim()
            if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { return }
            $k, $v = $line.Split("=", 2)
            $k = $k.Trim()
            $v = $v.Trim().Trim('"').Trim("'")
            if ($k -in @(
                    "DIFY_WEB_PORT", "DIFY_DIR", "DIFY_GIT_REF",
                    "AI_GATEWAY_URL", "LITELLM_MASTER_KEY"
                )) {
                Set-Item -Path "Env:$k" -Value $v
            }
        }
    }
    if ($env:DIFY_DIR -and $env:DIFY_DIR.Trim()) {
        $script:DifyHome = $env:DIFY_DIR.Trim()
        $script:DifyRepo = Join-Path $script:DifyHome "repo"
        $script:DifyDocker = Join-Path $script:DifyRepo "docker"
    }
    if (-not $env:DIFY_WEB_PORT) { $env:DIFY_WEB_PORT = "3003" }
    if (-not $env:DIFY_GIT_REF) { $env:DIFY_GIT_REF = $script:DifyDefaultRef }
    if (-not $env:AI_GATEWAY_URL) { $env:AI_GATEWAY_URL = "http://127.0.0.1:8080" }
}

function Get-DifyDockerEnvPath {
    return (Join-Path $script:DifyDocker ".env")
}

function Set-DifyEnvKey {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )
    if (-not (Test-Path $Path)) {
        Write-Error "Missing Dify docker .env: $Path"
    }
    $lines = Get-Content $Path
    $found = $false
    $out = foreach ($line in $lines) {
        if ($line -match "^\s*#") { $line; continue }
        if ($line -match "^\s*$") { $line; continue }
        if ($line -match "^(\s*)$([regex]::Escape($Key))\s*=") {
            $found = $true
            "${Key}=${Value}"
        } else {
            $line
        }
    }
    if (-not $found) {
        $out = @($out) + "${Key}=${Value}"
    }
    Set-Content -Path $Path -Value $out -Encoding utf8
}

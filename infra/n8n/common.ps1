# Shared helpers for n8n (native Windows).
# Dot-source from other scripts in this folder.

$script:N8nHome = Join-Path $env:LOCALAPPDATA "AlexsoftN8n"
$script:N8nPrefix = Join-Path $script:N8nHome "prefix"
$script:N8nBin = Join-Path $script:N8nPrefix "node_modules\.bin"
$script:N8nCli = Join-Path $script:N8nBin "n8n.cmd"
$script:N8nPidFile = Join-Path $script:N8nHome "n8n.pid"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-RepoRootMarker {
    param([string]$HomeDir)
    $repoRoot = Get-RepoRoot
    Set-Content -Path (Join-Path $HomeDir "repo-root.txt") -Value $repoRoot -Encoding utf8
}

function Find-NodeMajor {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) { return $null }
    $ver = & node -v 2>$null
    if (-not $ver) { return $null }
    # v20.19.0 → 20
    if ($ver -match '^v?(\d+)\.') { return [int]$Matches[1] }
    return $null
}

function Assert-NodeForN8n {
    $major = Find-NodeMajor
    if ($null -eq $major) {
        Write-Error "Node.js not found. Install Node.js 20.19-24.x (LTS), then re-run."
    }
    if ($major -lt 20 -or $major -gt 24) {
        Write-Error "n8n needs Node.js 20.19-24.x (found major $major). Upgrade/downgrade Node, then re-run."
    }
    $full = (& node -v).Trim()
    Write-Host "Using Node $full"
}

function Import-N8nEnv {
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
                    "N8N_HOST", "N8N_PORT",
                    "AI_GATEWAY_URL", "LITELLM_MASTER_KEY"
                )) {
                Set-Item -Path "Env:$k" -Value $v
            }
        }
    }
    if (-not $env:N8N_HOST) { $env:N8N_HOST = "127.0.0.1" }
    if (-not $env:N8N_PORT) { $env:N8N_PORT = "5678" }
    if (-not $env:AI_GATEWAY_URL) { $env:AI_GATEWAY_URL = "http://127.0.0.1:8080" }
    # n8n user folder under AlexsoftN8n (not %USERPROFILE%\.n8n) for isolation.
    $env:N8N_USER_FOLDER = Join-Path $script:N8nHome "data"
    New-Item -ItemType Directory -Force -Path $env:N8N_USER_FOLDER | Out-Null
}

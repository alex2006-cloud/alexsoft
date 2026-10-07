# Shared helpers for Authentik (Docker Compose, DB in native Postgres). Dot-source from sibling scripts.

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            $v = $Matches[1].Trim().Trim('"').Trim("'")
            if ($v) { return $v }
            return $Default
        }
    }
    return $Default
}

function Set-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Value)
    $raw = if (Test-Path $Path) { Get-Content -Raw -Path $Path } else { "" }
    if ($raw -match "(?m)^\s*$Key\s*=") {
        $updated = [regex]::Replace($raw, "(?m)^\s*$Key\s*=.*$", { param($m) "$Key=$Value" })
        Set-Content -Path $Path -Value $updated.TrimEnd() -Encoding utf8
    } else {
        Add-Content -Path $Path -Value "`n$Key=$Value" -Encoding utf8
    }
}

function New-RandomSecret {
    param([int]$Length = 48)
    $chars = [char[]]"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $bytes = New-Object byte[] ($Length)
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return -join ($bytes | ForEach-Object { $chars[$_ % $chars.Length] })
}

function Find-Psql {
    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    foreach ($c in @(
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    )) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

function New-ComposeEnvFile {
    # docker compose rejects the whole .env if any line is malformed (e.g. "license key=..."),
    # so compose gets a filtered copy with valid KEY=VALUE lines only (kept outside the repo).
    param([string]$Source)
    $dir = Join-Path $env:LOCALAPPDATA "AlexsoftAuthentik"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $target = Join-Path $dir "compose.env"
    Get-Content -LiteralPath $Source |
        Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_.-]*\s*=' } |
        Set-Content -LiteralPath $target -Encoding utf8
    return $target
}

function Test-DockerReady {
    # docker writes to stderr when the daemon is down; with $ErrorActionPreference=Stop that would throw.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & docker info 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    finally { $ErrorActionPreference = $prev }
}

function Start-DockerDesktopIfNeeded {
    param([int]$TimeoutSeconds = 180)
    if (Test-DockerReady) { return }
    $exe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $exe)) { Write-Error "Docker Desktop not found. Install it first (Authentik runs in Compose, ADR-0020)." }
    Write-Host "Starting Docker Desktop ..."
    Start-Process -FilePath $exe | Out-Null
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if (Test-DockerReady) { return }
    }
    Write-Error "Docker did not become ready within $TimeoutSeconds s."
}

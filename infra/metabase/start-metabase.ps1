# Start local Metabase (HTTP UI, default :3002 — landing :3000, Grafana :3001). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\metabase\start-metabase.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$metabaseHome = Join-Path $env:LOCALAPPDATA "Metabase"
$jarPath = Join-Path $metabaseHome "metabase.jar"
$stdoutLog = Join-Path $metabaseHome "metabase.out.log"
$stderrLog = Join-Path $metabaseHome "metabase.err.log"
$pidFile = Join-Path $metabaseHome "metabase.pid"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key=(.*)$") {
            return $Matches[1].Trim()
        }
    }
    return $Default
}

function Find-JavaExe {
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }

    $roots = @(
        (Join-Path $env:ProgramFiles "Eclipse Adoptium"),
        (Join-Path ${env:ProgramFiles(x86)} "Eclipse Adoptium"),
        (Join-Path $env:LOCALAPPDATA "Programs\Eclipse Adoptium")
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $roots) {
        $found = Get-ChildItem -Path $root -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\bin\\java\.exe$' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    return $null
}

if (-not (Test-Path $jarPath)) {
    Write-Error "metabase.jar not found at $jarPath. Run install-metabase.ps1 first."
}

$javaExe = Find-JavaExe
if (-not $javaExe) {
    Write-Error "Java not found. Install Eclipse Temurin JRE 25+ (winget: EclipseAdoptium.Temurin.25.JRE)."
}

$port = Read-DotEnvValue -Path $envFile -Key "METABASE_PORT" -Default "3002"
$hostBind = Read-DotEnvValue -Path $envFile -Key "METABASE_HOST" -Default "127.0.0.1"
if ($hostBind -eq "localhost") { $hostBind = "127.0.0.1" }

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Metabase already listening on ${hostBind}:$port (PID $($listen.OwningProcess))"
    Write-Host "UI:     http://127.0.0.1:$port"
    Write-Host "Setup:  http://127.0.0.1:$port/setup"
    Write-Host "Health: http://127.0.0.1:$port/api/health"
    exit 0
}

New-Item -ItemType Directory -Force -Path $metabaseHome | Out-Null

$env:MB_JETTY_HOST = $hostBind
$env:MB_JETTY_PORT = $port

# Use relative JAR name: absolute Windows paths become "/C:/..." URIs and break
# Metabase plugin bootstrap (Illegal char <:>). WorkingDirectory is metabaseHome.
$pluginsDir = Join-Path $metabaseHome "plugins"
New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null
$env:MB_PLUGINS_DIR = $pluginsDir

$javaArgs = @(
    "--add-opens", "java.base/java.nio=ALL-UNNAMED",
    "-jar", "metabase.jar"
)

$proc = Start-Process -FilePath $javaExe -ArgumentList $javaArgs -WorkingDirectory $metabaseHome `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog `
    -WindowStyle Hidden -PassThru

Set-Content -Path $pidFile -Value $proc.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(180)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 1000
    if ($proc.HasExited) {
        Write-Error "Metabase process exited early (code $($proc.ExitCode)). See $stdoutLog and $stderrLog"
    }
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if (-not $up) { continue }
    try {
        $body = & curl.exe -s --max-time 3 "http://127.0.0.1:$port/api/health"
        if ($body -match '"status"\s*:\s*"ok"' -or $body -match '"status"') {
            $ready = $true
            break
        }
    } catch {
        # warming up
    }
}

if (-not $ready) {
    Write-Error "Metabase did not become ready on port $port within 180s. See $stdoutLog and $stderrLog"
}

Write-Host "Metabase started (PID $($proc.Id))"
Write-Host "UI:      http://127.0.0.1:$port"
Write-Host "Setup:   http://127.0.0.1:$port/setup"
Write-Host "Health:  http://127.0.0.1:$port/api/health"
Write-Host "Java:    $javaExe"
Write-Host "JAR:     $jarPath"
Write-Host "Data:    $metabaseHome (H2 app DB + plugins)"
Write-Host "Log:     $stdoutLog"
Write-Host "Next:    open Setup in browser, then connect PostgreSQL alexsoft (separate step)."

# Start local Grafana (HTTP UI, default :3001 — landing keeps :3000). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\grafana\start-grafana.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$dsTemplate = Join-Path $scriptDir "provisioning\datasources\alexsoft.yml.template"
$dashTemplate = Join-Path $scriptDir "provisioning\dashboards\dashboards.yml.template"
$dashJsonSrc = Join-Path $scriptDir "provisioning\dashboards\json"
$grafanaHome = Join-Path $env:LOCALAPPDATA "Grafana"
$dataDir = Join-Path $grafanaHome "data"
$logDir = Join-Path $grafanaHome "log"
$pluginsDir = Join-Path $grafanaHome "plugins"
$provisioningDir = Join-Path $grafanaHome "provisioning"
$dsDir = Join-Path $provisioningDir "datasources"
$dashDir = Join-Path $provisioningDir "dashboards"
$dashJsonDir = Join-Path $dashDir "json"
$stdoutLog = Join-Path $grafanaHome "grafana.out.log"
$stderrLog = Join-Path $grafanaHome "grafana.err.log"

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

function Find-GrafanaExe {
    param([string]$Root)
    foreach ($name in @("grafana.exe", "grafana-server.exe")) {
        $p = Join-Path $Root "bin\$name"
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Write-ProvisioningFiles {
    param(
        [string]$PrometheusPort,
        [string]$LokiPort
    )
    if (-not (Test-Path $dsTemplate)) {
        Write-Error "Datasource template not found: $dsTemplate"
    }
    if (-not (Test-Path $dashTemplate)) {
        Write-Error "Dashboards template not found: $dashTemplate"
    }
    if (-not (Test-Path $dashJsonSrc)) {
        Write-Error "Dashboard JSON folder not found: $dashJsonSrc"
    }

    New-Item -ItemType Directory -Force -Path $dsDir | Out-Null
    New-Item -ItemType Directory -Force -Path $dashJsonDir | Out-Null

    $dsText = Get-Content -Raw -Path $dsTemplate
    $dsText = $dsText.Replace("__PROMETHEUS_PORT__", $PrometheusPort)
    $dsText = $dsText.Replace("__LOKI_PORT__", $LokiPort)
    [System.IO.File]::WriteAllText((Join-Path $dsDir "alexsoft.yml"), $dsText)

    $jsonPathForYaml = ($dashJsonDir -replace "\\", "/")
    $dashText = Get-Content -Raw -Path $dashTemplate
    $dashText = $dashText.Replace("__DASHBOARDS_JSON_DIR__", $jsonPathForYaml)
    [System.IO.File]::WriteAllText((Join-Path $dashDir "dashboards.yml"), $dashText)

    Copy-Item -Path (Join-Path $dashJsonSrc "*.json") -Destination $dashJsonDir -Force
}

$grafanaExe = Find-GrafanaExe -Root $grafanaHome
if (-not $grafanaExe) {
    Write-Error "Grafana binary not found under $grafanaHome\bin. Run install-grafana.ps1 first."
}

$port = Read-DotEnvValue -Path $envFile -Key "GRAFANA_PORT" -Default "3001"
$adminUser = Read-DotEnvValue -Path $envFile -Key "GRAFANA_ADMIN_USER" -Default "admin"
$adminPassword = Read-DotEnvValue -Path $envFile -Key "GRAFANA_ADMIN_PASSWORD" -Default "change-me"
$promPort = Read-DotEnvValue -Path $envFile -Key "PROMETHEUS_PORT" -Default "9090"
$lokiPort = Read-DotEnvValue -Path $envFile -Key "LOKI_PORT" -Default "3100"

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null

Write-ProvisioningFiles -PrometheusPort $promPort -LokiPort $lokiPort

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "Grafana already listening on 127.0.0.1:$port (PID $($listen.OwningProcess))"
    Write-Host "UI:            http://127.0.0.1:$port"
    Write-Host "Dashboards:    http://127.0.0.1:$port/d/alexsoft-cpu"
    Write-Host "               http://127.0.0.1:$port/d/alexsoft-pg-logs"
    Write-Host "               http://127.0.0.1:$port/d/alexsoft-pg-changes"
    Write-Host "Provisioning updated under $provisioningDir"
    Write-Host "Restart Grafana (stop + start) to load new dashboards/datasources."
    exit 0
}

$env:GF_SERVER_HTTP_ADDR = "127.0.0.1"
$env:GF_SERVER_HTTP_PORT = $port
$env:GF_SERVER_DOMAIN = "localhost"
$env:GF_SERVER_ROOT_URL = "http://127.0.0.1:$port/"
$env:GF_SECURITY_ADMIN_USER = $adminUser
$env:GF_SECURITY_ADMIN_PASSWORD = $adminPassword
$env:GF_SECURITY_DISABLE_INITIAL_ADMIN_PASSWORD_CHANGE = "true"
$env:GF_PATHS_DATA = $dataDir
$env:GF_PATHS_LOGS = $logDir
$env:GF_PATHS_PLUGINS = $pluginsDir
$env:GF_PATHS_PROVISIONING = $provisioningDir
$env:GF_ANALYTICS_REPORTING_ENABLED = "false"
$env:GF_ANALYTICS_CHECK_FOR_UPDATES = "false"
$env:GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES = "false"

$exeName = [System.IO.Path]::GetFileNameWithoutExtension($grafanaExe)
$argList = @()
if ($exeName -eq "grafana") {
    $argList = @("server", "--homepath", $grafanaHome)
} else {
    $argList = @("--homepath", $grafanaHome)
}

$proc = Start-Process -FilePath $grafanaExe -ArgumentList $argList -WorkingDirectory $grafanaHome `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(60)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 700
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if (-not $up) { continue }
    try {
        $body = & curl.exe -s --max-time 2 "http://127.0.0.1:$port/api/health"
        if ($body -match '"database"\s*:\s*"ok"') {
            $ready = $true
            break
        }
    } catch {
        # warming up
    }
}

if (-not $ready) {
    Write-Error "Grafana did not become ready on port $port. See $stdoutLog and $stderrLog"
}

Write-Host "Grafana started (PID $($proc.Id))"
Write-Host "UI:          http://127.0.0.1:$port"
Write-Host "Dashboard:   http://127.0.0.1:$port/d/alexsoft-cpu"
Write-Host "             http://127.0.0.1:$port/d/alexsoft-pg-logs"
Write-Host "             http://127.0.0.1:$port/d/alexsoft-pg-changes"
Write-Host "Health:      http://127.0.0.1:$port/api/health"
Write-Host "Login:       $adminUser / (GRAFANA_ADMIN_PASSWORD from .env)"
Write-Host "Datasources: Prometheus (:$promPort), Loki (:$lokiPort)"
Write-Host "Data:        $dataDir"
Write-Host "Log:         $stdoutLog"

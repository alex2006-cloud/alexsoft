# Start local LiteLLM proxy (default :8080). See README.md / ADR-0011.
# powershell -ExecutionPolicy Bypass -File infra\litellm\start-litellm.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$configSrc = Join-Path $scriptDir "config.yaml"
$litellmHome = Join-Path $env:LOCALAPPDATA "LiteLLM"
$venvPython = Join-Path $litellmHome "venv\Scripts\python.exe"
$litellmCli = Join-Path $litellmHome "venv\Scripts\litellm.exe"
$runProxySrc = Join-Path $scriptDir "run-proxy.py"
$runProxyDst = Join-Path $litellmHome "run-proxy.py"
$configDst = Join-Path $litellmHome "config.yaml"
$stdoutLog = Join-Path $litellmHome "litellm.out.log"
$stderrLog = Join-Path $litellmHome "litellm.err.log"
$pidFile = Join-Path $litellmHome "litellm.pid"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

function Import-DotEnvKeys {
    param(
        [string]$Path,
        [string[]]$Keys
    )
    if (-not (Test-Path $Path)) { return }
    $wanted = @{}
    foreach ($k in $Keys) { $wanted[$k] = $true }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$") {
            $k = $Matches[1]
            if (-not $wanted.ContainsKey($k)) { continue }
            $v = $Matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
}

if (-not (Test-Path $litellmCli) -and -not (Test-Path $venvPython)) {
    Write-Error "LiteLLM not installed at $litellmHome. Run install-litellm.ps1 first."
}
if (-not (Test-Path $configSrc)) {
    Write-Error "Missing config: $configSrc"
}
if (-not (Test-Path $runProxySrc)) {
    Write-Error "Missing runner: $runProxySrc"
}

# Only AI-related keys. Use LITELLM_DATABASE_URL (not alexsoft DATABASE_URL).
Import-DotEnvKeys -Path $envFile -Keys @(
    "LITELLM_HOST",
    "LITELLM_PORT",
    "LITELLM_MASTER_KEY",
    "LITELLM_DATABASE_URL",
    "LITELLM_SALT_KEY",
    "STORE_MODEL_IN_DB",
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_API_BASE",
    "AI_GATEWAY_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY"
)

$hostBind = Read-DotEnvValue -Path $envFile -Key "LITELLM_HOST" -Default "127.0.0.1"
if ($hostBind -eq "localhost") { $hostBind = "127.0.0.1" }
$port = Read-DotEnvValue -Path $envFile -Key "LITELLM_PORT" -Default "8080"

$deepKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "Process")
if (-not $deepKey) {
    Write-Warning "DEEPSEEK_API_KEY is empty. Proxy will start, but DeepSeek calls will fail until you set it in .env."
}

$dashKey = [Environment]::GetEnvironmentVariable("DASHSCOPE_API_KEY", "Process")
if (-not $dashKey) {
    Write-Warning "DASHSCOPE_API_KEY is empty. Qwen calls will fail until you set it in .env (optional)."
}

$apiBase = [Environment]::GetEnvironmentVariable("DASHSCOPE_API_BASE", "Process")
if (-not $apiBase) {
    $apiBase = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    [Environment]::SetEnvironmentVariable("DASHSCOPE_API_BASE", $apiBase, "Process")
}

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "LiteLLM already on port $port - stopping before restart (so .env changes apply) ..."
    & powershell -ExecutionPolicy Bypass -File (Join-Path $scriptDir "stop-litellm.ps1")
    Start-Sleep -Milliseconds 800
}

$masterKey = [Environment]::GetEnvironmentVariable("LITELLM_MASTER_KEY", "Process")
if (-not $masterKey) {
    Write-Warning "LITELLM_MASTER_KEY is empty. Admin UI login will fail until you set it in .env and restart."
}

$litellmDb = [Environment]::GetEnvironmentVariable("LITELLM_DATABASE_URL", "Process")
$skipDb = [Environment]::GetEnvironmentVariable("LITELLM_SKIP_DB", "Process")
if ($skipDb -eq "1") {
    Write-Warning "LITELLM_SKIP_DB=1 - starting API without Prisma/Admin UI DB."
    $litellmDb = $null
    [Environment]::SetEnvironmentVariable("LITELLM_DATABASE_URL", $null, "Process")
}
if (-not $litellmDb) {
    Write-Warning "LITELLM_DATABASE_URL is empty. Admin UI needs Postgres - run setup-db.ps1 (or set LITELLM_SKIP_DB=1 for API-only)."
}

New-Item -ItemType Directory -Force -Path $litellmHome | Out-Null
Copy-Item -Force -Path $configSrc -Destination $configDst
Copy-Item -Force -Path $runProxySrc -Destination $runProxyDst
Set-Content -Path (Join-Path $litellmHome "repo-root.txt") -Value $repoRoot -Encoding ascii

[Environment]::SetEnvironmentVariable("LITELLM_LOCAL_MODEL_COST_MAP", "True", "Process")
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "Process")
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "Process")
# Map dedicated LiteLLM DB URL into the name Prisma expects. Never use alexsoft DATABASE_URL.
if ($litellmDb) {
    [Environment]::SetEnvironmentVariable("DATABASE_URL", $litellmDb, "Process")
} else {
    [Environment]::SetEnvironmentVariable("DATABASE_URL", $null, "Process")
}
# Schema applied via setup-prisma/db push; avoid broken migrate deploy on shared-schema setups.
[Environment]::SetEnvironmentVariable("DISABLE_SCHEMA_UPDATE", "true", "Process")
[Environment]::SetEnvironmentVariable("DIRECT_URL", $null, "Process")
[Environment]::SetEnvironmentVariable("PRISMA_SCHEMA", $null, "Process")

$argList = @(
    $runProxyDst,
    "--config", $configDst,
    "--host", $hostBind,
    "--port", $port
)
# Master key: LITELLM_MASTER_KEY env + general_settings.master_key in config.yaml
# (CLI flag --master_key is not available in current litellm proxy).

$proxyDir = Join-Path $litellmHome "venv\Lib\site-packages\litellm\proxy"
# WorkingDirectory must be the proxy package dir so prisma can find schema.prisma.
# Do NOT RedirectStandardOutput/Error via Start-Process: breaks Prisma query-engine on Windows.
$proc = Start-Process -FilePath $venvPython -ArgumentList $argList -WorkingDirectory $proxyDir `
    -WindowStyle Minimized -PassThru

Set-Content -Path $pidFile -Value $proc.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(120)
$ready = $false
$exitGrace = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    $up = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
    if ($up) {
        try {
            $body = & curl.exe -s --max-time 3 "http://127.0.0.1:$port/health/liveliness"
            if (-not $body) {
                $body = & curl.exe -s --max-time 3 "http://127.0.0.1:$port/health"
            }
            if ($body) {
                $ready = $true
                $listenPid = ($up | Select-Object -First 1 -ExpandProperty OwningProcess)
                if ($listenPid) {
                    Set-Content -Path $pidFile -Value $listenPid -Encoding ascii
                }
                break
            }
        } catch {
            # warming up
        }
    }
    if ($proc.HasExited -and -not $up -and (Get-Date) -gt $exitGrace) {
        $bootLog = Join-Path $litellmHome "boot.log"
        Write-Error "LiteLLM exited early (code $($proc.ExitCode)) before port $port. See $bootLog"
    }
}

if (-not $ready) {
    $code = if ($proc.HasExited) { $proc.ExitCode } else { "running-but-not-ready" }
    $bootLog = Join-Path $litellmHome "boot.log"
    Write-Error "LiteLLM did not become ready on port $port within 120s (proc=$code). See $bootLog"
}

Write-Host "LiteLLM started (PID $($proc.Id))"
Write-Host "URL:     http://127.0.0.1:$port"
Write-Host "UI:      http://127.0.0.1:$port/ui"
Write-Host "Health:  http://127.0.0.1:$port/health"
Write-Host "Model:   qwen -> dashscope/qwen-plus"
Write-Host "Config:  $configDst"
Write-Host "Log:     $stdoutLog"
Write-Host "API base:$apiBase"
if ($masterKey) {
    Write-Host "Master:  LITELLM_MASTER_KEY is set (UI login: admin / that value)"
} else {
    Write-Host "Master:  NOT set - Admin UI will reject login"
}
if ($litellmDb) {
    Write-Host "DB:      LITELLM_DATABASE_URL is set (Admin UI Prisma)"
} else {
    Write-Host "DB:      NOT set - Admin UI needs setup-db.ps1"
}

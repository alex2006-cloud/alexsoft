# Start n8n UI on 127.0.0.1:5678
# powershell -ExecutionPolicy Bypass -File infra\n8n\start-n8n.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:N8nCli)) {
    Write-Error "n8n not installed. Run install-n8n.ps1 first."
}

Import-N8nEnv

$hostName = $env:N8N_HOST
$port = [int]$env:N8N_PORT

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$env:N8N_HOST = $hostName
$env:N8N_PORT = "$port"
$env:N8N_LISTEN_ADDRESS = $hostName
$env:N8N_EDITOR_BASE_URL = "http://${hostName}:${port}/"

# Prefer node entrypoint: Start-Process + Redirect on .cmd often exits immediately on Windows.
$n8nJs = Join-Path $script:N8nPrefix "node_modules\n8n\bin\n8n"
if (-not (Test-Path $n8nJs)) {
    Write-Error "n8n entry missing: $n8nJs"
}
$nodeExe = (Get-Command node -ErrorAction Stop).Source
$outLog = Join-Path $script:N8nHome "n8n.out.log"
$errLog = Join-Path $script:N8nHome "n8n.err.log"

Write-Host "Starting n8n on http://${hostName}:$port ..."
$proc = Start-Process -FilePath $nodeExe -ArgumentList @($n8nJs, "start") `
    -WorkingDirectory $script:N8nPrefix -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog
Set-Content -Path $script:N8nPidFile -Value $proc.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(180)
$ok = $false
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) {
        $tail = ""
        if (Test-Path $errLog) { $tail = (Get-Content $errLog -Raw) }
        Write-Error "n8n exited early (code $($proc.ExitCode)). Log: $errLog`n$tail"
    }
    try {
        $r = Invoke-WebRequest -Uri "http://${hostName}:$port/healthz" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {
        try {
            $r2 = Invoke-WebRequest -Uri "http://${hostName}:$port/" -UseBasicParsing -TimeoutSec 3
            if ($r2.StatusCode -ge 200 -and $r2.StatusCode -lt 500) { $ok = $true; break }
        } catch { }
    }
    Start-Sleep -Seconds 2
}

if (-not $ok) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    $tail = ""
    if (Test-Path $errLog) { $tail = (Get-Content $errLog -Tail 30) -join "`n" }
    Write-Error "n8n did not become ready on :$port within timeout.`n$tail"
}

Write-Host "n8n started (PID $($proc.Id))"
Write-Host "UI: http://${hostName}:$port"
Write-Host "LiteLLM: OpenAI credential -> $($env:AI_GATEWAY_URL.TrimEnd('/'))/v1 + LITELLM_MASTER_KEY"

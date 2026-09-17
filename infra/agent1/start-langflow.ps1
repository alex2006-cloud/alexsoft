# Start LangFlow UI on 127.0.0.1:7860
# powershell -ExecutionPolicy Bypass -File infra\agent1\start-langflow.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:LangFlowPython)) {
    Write-Error "LangFlow venv missing. Run install-langflow.ps1 first."
}

$port = 7860
if ($env:LANGFLOW_PORT) { $port = [int]$env:LANGFLOW_PORT }
$hostName = "127.0.0.1"
if ($env:LANGFLOW_HOST) { $hostName = $env:LANGFLOW_HOST }

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$lf = Join-Path $script:LangFlowVenv "Scripts\langflow.exe"
$pidFile = Join-Path $script:LangFlowHome "langflow.pid"

if (Test-Path $lf) {
    $filePath = $lf
    $argList = @("run", "--host", $hostName, "--port", "$port")
} else {
    $filePath = $script:LangFlowPython
    $argList = @("-m", "langflow", "run", "--host", $hostName, "--port", "$port")
}

Write-Host "Starting LangFlow on http://${hostName}:$port ..."
$proc = Start-Process -FilePath $filePath -ArgumentList $argList `
    -WorkingDirectory $script:LangFlowHome -WindowStyle Minimized -PassThru
Set-Content -Path $pidFile -Value $proc.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(180)
$ok = $false
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) {
        Write-Error "LangFlow exited early (code $($proc.ExitCode))."
    }
    try {
        $r = Invoke-WebRequest -Uri "http://${hostName}:$port/" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ok = $true; break }
    } catch {
        try {
            $r2 = Invoke-WebRequest -Uri "http://${hostName}:$port/health" -UseBasicParsing -TimeoutSec 3
            if ($r2.StatusCode -eq 200) { $ok = $true; break }
        } catch { }
    }
    Start-Sleep -Seconds 3
}

if (-not $ok) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Write-Error "LangFlow did not become ready on :$port within timeout."
}

Write-Host "LangFlow started (PID $($proc.Id))"
Write-Host "UI: http://${hostName}:$port"
Write-Host "Wire LiteLLM in UI: OpenAI-compatible base URL = AI_GATEWAY_URL/v1, model = deepseek, key = LITELLM_MASTER_KEY"

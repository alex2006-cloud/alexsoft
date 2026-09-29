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

$repoRoot = Get-RepoRoot
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { return }
        $k, $v = $line.Split("=", 2)
        $k = $k.Trim()
        $v = $v.Trim().Trim('"').Trim("'")
        if ($k -in @("AI_GATEWAY_URL")) { Set-Item -Path "Env:$k" -Value $v }
    }
}
if (-not $env:AI_GATEWAY_URL) { $env:AI_GATEWAY_URL = "http://127.0.0.1:8080" }

# Agent1 components (Alexsoft Calculator) + LiteLLM as the "OpenAI Compatible" provider.
# The provider's API key is a LangFlow global variable, set by langflow-build-qa-flow.ps1.
$env:LANGFLOW_COMPONENTS_PATH = Join-Path $repoRoot "apps\agent1\langflow\components"
$env:ALEXSOFT_AGENT1_DIR = Join-Path $repoRoot "apps\agent1"
$env:OPENAI_COMPATIBLE_BASE_URL = ($env:AI_GATEWAY_URL.TrimEnd("/") + "/v1")

Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$runSrc = Join-Path $PSScriptRoot "run-langflow.py"
$runDst = Join-Path $script:LangFlowHome "run-langflow.py"
if (-not (Test-Path $runSrc)) {
    Write-Error "Missing runner: $runSrc"
}
Copy-Item -Force $runSrc $runDst

$pidFile = Join-Path $script:LangFlowHome "langflow.pid"
$filePath = $script:LangFlowPython
$argList = @($runDst, "run", "--host", $hostName, "--port", "$port")

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
Write-Host "LiteLLM provider: OpenAI Compatible, base URL $env:OPENAI_COMPATIBLE_BASE_URL"
Write-Host "Agent1 components: $env:LANGFLOW_COMPONENTS_PATH"
Write-Host "Build the agent1_qa flow: infra\agent1\langflow-build-qa-flow.ps1"

# Agent1 Q&A + calculator product (LangGraph graph agent1_qa) in the terminal.
# Requires LiteLLM running and the Agent1 venv.
# powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1
# powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1 --once "2^10 + sqrt(16)"

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent1Python)) {
    Write-Error "Agent1 venv missing. Run infra\agent1\install-langgraph.ps1 first."
}

$repoRoot = Get-RepoRoot
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { return }
        $k, $v = $line.Split("=", 2)
        $k = $k.Trim()
        $v = $v.Trim().Trim('"').Trim("'")
        if ($k -in @("AI_GATEWAY_URL", "LITELLM_MASTER_KEY", "AGENT1_MODEL", "LANGSMITH_TRACING")) {
            Set-Item -Path "Env:$k" -Value $v
        }
    }
}

if (-not $env:AI_GATEWAY_URL) { $env:AI_GATEWAY_URL = "http://127.0.0.1:8080" }
$env:OPENAI_BASE_URL = ($env:AI_GATEWAY_URL.TrimEnd("/") + "/v1")
if ($env:LITELLM_MASTER_KEY) { $env:OPENAI_API_KEY = $env:LITELLM_MASTER_KEY }
if (-not $env:AGENT1_MODEL) { $env:AGENT1_MODEL = "deepseek" }
$env:LANGSMITH_TRACING = "false"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Quick gateway check
try {
    $null = Invoke-WebRequest -Uri "$($env:AI_GATEWAY_URL.TrimEnd('/'))/health/liveliness" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Warning "LiteLLM liveliness check failed - is the gateway running?"
}

$chat = Join-Path $PSScriptRoot "chat-qa.py"
& $script:Agent1Python $chat @args
exit $LASTEXITCODE

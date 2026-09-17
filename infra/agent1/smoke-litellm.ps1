# Smoke: Agent1 graph_llm → LiteLLM (model qwen).
# Requires LiteLLM running and Agent1 venv with langchain-openai.
# powershell -ExecutionPolicy Bypass -File infra\agent1\smoke-litellm.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent1Python)) {
    Write-Error "Agent1 venv missing."
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
if (-not $env:AGENT1_MODEL) { $env:AGENT1_MODEL = "qwen" }
$env:LANGSMITH_TRACING = "false"

# Quick gateway check
try {
    $null = Invoke-WebRequest -Uri "$($env:AI_GATEWAY_URL.TrimEnd('/'))/health/liveliness" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Warning "LiteLLM liveliness check failed — is the gateway running?"
}

$smoke = Join-Path $PSScriptRoot "smoke-litellm.py"
& $script:Agent1Python $smoke
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Warning "Smoke failed (exit $code). If DashScope returns 401, fix DASHSCOPE_API_KEY / region — Agent1 wiring is still valid."
    exit $code
}
Write-Host "smoke-litellm OK"

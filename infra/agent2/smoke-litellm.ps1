# Smoke: Agent2 make_llm → LiteLLM (one short completion).
# Requires LiteLLM running and Agent2 venv with crewai.
# powershell -ExecutionPolicy Bypass -File infra\agent2\smoke-litellm.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent2Python)) {
    Write-Error "Agent2 venv missing. Run infra\agent2\install-crewai.ps1 first."
}

Import-Agent2Env

try {
    $null = Invoke-WebRequest -Uri "$($env:AI_GATEWAY_URL.TrimEnd('/'))/health/liveliness" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Warning "LiteLLM liveliness check failed - is the gateway running?"
}

$smoke = Join-Path $PSScriptRoot "smoke-litellm.py"
& $script:Agent2Python $smoke
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Warning "Smoke failed (exit $code). Check DEEPSEEK_API_KEY (or AGENT2_MODEL/qwen + DASHSCOPE) and that LiteLLM is up."
    exit $code
}
Write-Host "smoke-litellm OK"

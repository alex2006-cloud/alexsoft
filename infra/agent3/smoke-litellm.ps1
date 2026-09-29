# Smoke: Agent3 make_model_client → LiteLLM (one short completion).
# Requires LiteLLM running and Agent3 venv with AutoGen.
# powershell -ExecutionPolicy Bypass -File infra\agent3\smoke-litellm.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent3Python)) {
    Write-Error "Agent3 venv missing. Run infra\agent3\install-autogen.ps1 first."
}

Import-Agent3Env

try {
    $null = Invoke-WebRequest -Uri "$($env:AI_GATEWAY_URL.TrimEnd('/'))/health/liveliness" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Warning "LiteLLM liveliness check failed - is the gateway running?"
}

$smoke = Join-Path $PSScriptRoot "smoke-litellm.py"
& $script:Agent3Python $smoke
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Warning "Smoke failed (exit $code). Check DEEPSEEK_API_KEY (or AGENT3_MODEL/qwen + DASHSCOPE) and that LiteLLM is up."
    exit $code
}
Write-Host "smoke-litellm OK"

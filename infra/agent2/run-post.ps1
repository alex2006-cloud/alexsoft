# Agent2 post-draft product (CrewAI) in the terminal.
# Requires LiteLLM running and the Agent2 venv.
# powershell -ExecutionPolicy Bypass -File infra\agent2\run-post.ps1
# powershell -ExecutionPolicy Bypass -File infra\agent2\run-post.ps1 --once "Topic here"

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

$runner = Join-Path $PSScriptRoot "run-post.py"
& $script:Agent2Python $runner @args
exit $LASTEXITCODE

# Step 2: install LangGraph into the Agent1 venv + smoke (no LLM).
# powershell -ExecutionPolicy Bypass -File infra\agent1\install-langgraph.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent1Python)) {
    Write-Error "Agent1 venv missing. Run install-langchain.ps1 first."
}

Ensure-PipReady

Write-Host "Installing langgraph ..."
& $script:Agent1Python -m pip install "langgraph"
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install langgraph failed."
}

$smokePy = Join-Path $PSScriptRoot "smoke-langgraph.py"
Write-Host "Smoke: tiny graph (no LLM) ..."
& $script:Agent1Python $smokePy
if ($LASTEXITCODE -ne 0) {
    Write-Error "LangGraph smoke failed."
}

Write-Host ""
Write-Host "LangGraph OK"
Write-Host "Next: install-studio.ps1"

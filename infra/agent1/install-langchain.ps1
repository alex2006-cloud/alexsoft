# Step 1: create Agent1 venv + install LangChain only.
# powershell -ExecutionPolicy Bypass -File infra\agent1\install-langchain.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Ensure-Agent1Venv
Ensure-PipReady
Write-RepoRootMarker -HomeDir $script:Agent1Home

Write-Host "Installing langchain ..."
& $script:Agent1Python -m pip install "langchain"
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install langchain failed."
}

Write-Host "Smoke: import langchain ..."
$ver = & $script:Agent1Python -c "import langchain; print(langchain.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "LangChain import smoke failed."
}

Write-Host ""
Write-Host "LangChain OK (version $ver)"
Write-Host "venv: $script:Agent1Venv"
Write-Host "Next: install-langgraph.ps1 (only after this step succeeds)."

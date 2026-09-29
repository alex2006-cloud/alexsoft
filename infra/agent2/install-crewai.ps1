# Create Agent2 venv + install CrewAI.
# powershell -ExecutionPolicy Bypass -File infra\agent2\install-crewai.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Ensure-Agent2Venv
Ensure-PipReady
Write-RepoRootMarker -HomeDir $script:Agent2Home

Write-Host "Installing crewai ..."
& $script:Agent2Python -m pip install "crewai"
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install crewai failed."
}

Write-Host "Smoke: import crewai ..."
$ver = & $script:Agent2Python -c "import crewai; print(getattr(crewai, '__version__', 'ok'))"
if ($LASTEXITCODE -ne 0) {
    Write-Error "CrewAI import smoke failed."
}

Write-Host ""
Write-Host "CrewAI OK (version $ver)"
Write-Host "venv: $script:Agent2Venv"
Write-Host "Next: smoke-litellm.ps1 (LiteLLM must be running), then run-post.ps1"

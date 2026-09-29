# Create Agent3 venv + install AutoGen AgentChat.
# powershell -ExecutionPolicy Bypass -File infra\agent3\install-autogen.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Ensure-Agent3Venv
Ensure-PipReady
Write-RepoRootMarker -HomeDir $script:Agent3Home

Write-Host "Installing autogen-agentchat + autogen-ext[openai] ..."
& $script:Agent3Python -m pip install "autogen-agentchat" "autogen-ext[openai]"
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install AutoGen packages failed."
}

Write-Host "Smoke: import autogen_agentchat ..."
$ver = & $script:Agent3Python -c "import autogen_agentchat; print(getattr(autogen_agentchat, '__version__', 'ok'))"
if ($LASTEXITCODE -ne 0) {
    Write-Error "AutoGen import smoke failed."
}

Write-Host ""
Write-Host "AutoGen OK (version $ver)"
Write-Host "venv: $script:Agent3Venv"
Write-Host "Next: smoke-litellm.ps1 (LiteLLM must be running)"

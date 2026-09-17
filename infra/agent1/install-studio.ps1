# Step 3: LangSmith Studio local Agent Server (langgraph-cli[inmem]).
# powershell -ExecutionPolicy Bypass -File infra\agent1\install-studio.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:Agent1Python)) {
    Write-Error "Agent1 venv missing. Run install-langchain.ps1 then install-langgraph.ps1 first."
}

Ensure-PipReady

Write-Host "Installing langgraph-cli[inmem] + langchain-openai (via uv) ..."
# pip+SOCKS on this host can hit urllib3 PoolKey errors; uv is more reliable.
& $script:Agent1Python -m pip install "uv"
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install uv failed."
}
& $script:Agent1Python -m uv pip install "langgraph-cli[inmem]" "langchain-openai" "colorama"
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv pip install langgraph-cli / langchain-openai failed."
}

$cli = Join-Path $script:Agent1Venv "Scripts\langgraph.exe"
if (-not (Test-Path $cli)) {
    Write-Error "langgraph.exe not found at $cli"
}

$ver = & $cli --version 2>&1
Write-Host "CLI: $ver"

# Editable install of apps/agent1 so langgraph.json dependencies: ["."] resolve.
$repoRoot = Get-RepoRoot
$appDir = Join-Path $repoRoot "apps\agent1"
Write-Host "pip install -e apps/agent1 ..."
& $script:Agent1Python -m pip install -e $appDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Editable install of apps/agent1 failed."
}

Write-RepoRootMarker -HomeDir $script:Agent1Home

Write-Host ""
Write-Host "Studio CLI OK"
Write-Host "Start: powershell -ExecutionPolicy Bypass -File infra\agent1\start-studio.ps1"
Write-Host "API:   http://127.0.0.1:2024"
Write-Host "UI:    https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
Write-Host "Note:  LANGSMITH_API_KEY in .env needed for Studio GUI (optional for local API)."

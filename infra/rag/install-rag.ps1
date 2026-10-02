# Create venv and install apps/rag (editable, with dev extras) into %LOCALAPPDATA%\AlexsoftRag\venv.
# powershell -ExecutionPolicy Bypass -File infra\rag\install-rag.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

Ensure-RagVenv
Ensure-PipReady

$appDir = Join-Path (Get-RepoRoot) "apps\rag"
Write-Host "Installing $appDir ..."
& $script:RagPython -m pip install -e "$appDir[dev]"
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed" }

& $script:RagPython -c "import alexsoft_rag, fastembed, qdrant_client, llama_index.core as li; print('alexsoft_rag OK; llama-index-core', li.__version__)"
Write-Host ""
Write-Host "Next: infra\qdrant\start-qdrant.ps1, then infra\rag\start-rag.ps1"

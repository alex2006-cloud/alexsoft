# Eval of the BP1 agent (needs Studio :2024, RAG :8200, LiteLLM :8080).
# powershell -ExecutionPolicy Bypass -File infra\agent1\eval-bp1.ps1 [-v]
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
if (-not (Test-Path $script:Agent1Python)) { Write-Error "Agent1 venv missing. Run install-langchain.ps1 first." }
$env:PYTHONIOENCODING = "utf-8"
$script = Join-Path (Get-RepoRoot) "apps\agent1\eval\run_eval.py"
& $script:Agent1Python $script @args
exit $LASTEXITCODE

# Install repo git hooks (LangFlow auto-export on commit).
# powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $repoRoot
try {
    git config core.hooksPath infra/githooks
    Write-Host "core.hooksPath = infra/githooks"
    Write-Host "On each git commit, LangFlow flows are exported to apps/agent1/langflow/flows/ and staged."
    Write-Host "Run once now:"
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot "infra\agent1\export-langflow.ps1")
} finally {
    Pop-Location
}

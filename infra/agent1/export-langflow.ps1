# Export LangFlow workflows into apps/agent1/langflow/flows/ (for git).
# Safe to run anytime; skips Starter templates; redacts API keys in JSON.
# powershell -ExecutionPolicy Bypass -File infra\agent1\export-langflow.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$pyCandidates = @(
    (Join-Path $env:LOCALAPPDATA "LangFlow\venv\Scripts\python.exe"),
    (Join-Path $env:LOCALAPPDATA "langflow\venv\Scripts\python.exe"),
    (Join-Path $env:LOCALAPPDATA "AlexsoftAgent1\venv\Scripts\python.exe"),
    "python"
)
$python = $null
foreach ($c in $pyCandidates) {
    if ($c -eq "python") {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) { $python = $cmd.Source; break }
    } elseif (Test-Path $c) {
        $python = $c
        break
    }
}
if (-not $python) {
    Write-Host "No Python found; skip LangFlow export."
    exit 0
}

& $python (Join-Path $scriptDir "export-langflow.py")
exit $LASTEXITCODE

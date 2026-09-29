# Build the agent1_qa flow in LangFlow (Chat Input -> Agent + calculator -> Chat Output)
# powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-build-qa-flow.ps1 [-Ask "2+2"]

param(
    [string]$Ask = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (-not (Test-Path $script:LangFlowPython)) {
    Write-Error "LangFlow venv missing. Run install-langflow.ps1 first."
}

$port = 7860
if ($env:LANGFLOW_PORT) { $port = [int]$env:LANGFLOW_PORT }
$hostName = "127.0.0.1"
if ($env:LANGFLOW_HOST) { $hostName = $env:LANGFLOW_HOST }

try {
    $null = Invoke-WebRequest -Uri "http://${hostName}:$port/health" -UseBasicParsing -TimeoutSec 5
} catch {
    Write-Error "LangFlow is not responding on :$port. Run start-langflow.ps1 first."
}

$env:ALEXSOFT_REPO_ROOT = Get-RepoRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$script = Join-Path $PSScriptRoot "langflow-build-qa-flow.py"
$argList = @($script, "--host", $hostName, "--port", "$port")
if ($Ask) { $argList += @("--ask", $Ask) }

& $script:LangFlowPython @argList
if ($LASTEXITCODE -ne 0) {
    Write-Error "Flow build failed (exit $LASTEXITCODE)."
}

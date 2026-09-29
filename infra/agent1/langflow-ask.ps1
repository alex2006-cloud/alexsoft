# Ask the LangFlow agent1_qa flow from the CLI
# powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-ask.ps1 -Ask "sqrt(144) + 2**10"
# -File passes -Ask as one string, so ask follow-ups with a second call and the same -Session.

param(
    [Parameter(Mandatory = $true)]
    [string[]]$Ask,
    [string]$Session = "cli",
    [string]$Flow = "agent1_qa"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$Questions = $Ask

if (-not (Test-Path $script:LangFlowPython)) {
    Write-Error "LangFlow venv missing. Run install-langflow.ps1 first."
}

$port = 7860
if ($env:LANGFLOW_PORT) { $port = [int]$env:LANGFLOW_PORT }
$hostName = "127.0.0.1"
if ($env:LANGFLOW_HOST) { $hostName = $env:LANGFLOW_HOST }

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$script = Join-Path $PSScriptRoot "langflow-ask.py"
$argList = @($script, "--flow", $Flow, "--session", $Session, "--host", $hostName, "--port", "$port") + $Questions

& $script:LangFlowPython @argList
exit $LASTEXITCODE

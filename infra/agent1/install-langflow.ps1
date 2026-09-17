# Step 4: LangFlow in a separate venv (uv + Python 3.12).
# powershell -ExecutionPolicy Bypass -File infra\agent1\install-langflow.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

New-Item -ItemType Directory -Force -Path $script:LangFlowHome | Out-Null
Write-RepoRootMarker -HomeDir $script:LangFlowHome

$pythonExe = Find-Python312
if (-not $pythonExe) {
    Write-Error "Python 3.12 required for LangFlow. Install Python.Python.3.12 then re-run."
}

if (-not (Test-Path $script:LangFlowPython)) {
    Write-Host "Creating LangFlow venv: $script:LangFlowVenv"
    & $pythonExe -m venv $script:LangFlowVenv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $script:LangFlowPython)) {
        Write-Error "Failed to create LangFlow venv"
    }
} else {
    Write-Host "venv already present: $script:LangFlowVenv"
}

# Bootstrap PySocks for pip if needed
$socksOk = $false
try {
    & $script:LangFlowPython -c "import socks" 2>$null
    if ($LASTEXITCODE -eq 0) { $socksOk = $true }
} catch { }
if (-not $socksOk) {
    $wheels = Join-Path $script:LangFlowHome "wheels"
    New-Item -ItemType Directory -Force -Path $wheels | Out-Null
    $whl = Join-Path $wheels "PySocks-1.7.1-py3-none-any.whl"
    $whlUrl = "https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl"
    if (-not (Test-Path $whl)) {
        & curl.exe -L --fail --retry 3 -o $whl $whlUrl
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to download PySocks wheel" }
    }
    & $script:LangFlowPython -m pip install --no-index --find-links $wheels "PySocks==1.7.1"
}

Write-Host "Installing uv + langflow (this can take several minutes) ..."
& $script:LangFlowPython -m pip install --upgrade pip uv
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install uv into LangFlow venv"
}

$env:UV_HTTP_TIMEOUT = "300"
& $script:LangFlowPython -m uv pip install "langflow"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Retrying langflow install once (network / extract timeouts are common) ..."
    & $script:LangFlowPython -m uv pip install "langflow"
}
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If build failed on Windows, install Microsoft C++ Build Tools:"
    Write-Host "  https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    Write-Error "uv pip install langflow failed."
}

$lf = Join-Path $script:LangFlowVenv "Scripts\langflow.exe"
if (-not (Test-Path $lf)) {
    # some installs expose module only
    $check = & $script:LangFlowPython -c "import langflow; print('ok')"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "langflow not importable after install"
    }
    Write-Host "langflow module OK ($check); use: python -m langflow run"
} else {
    Write-Host "CLI: $lf"
}

Write-Host ""
Write-Host "LangFlow OK"
Write-Host "Start: powershell -ExecutionPolicy Bypass -File infra\agent1\start-langflow.ps1"
Write-Host "UI:    http://127.0.0.1:7860"

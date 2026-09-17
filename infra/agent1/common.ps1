# Shared helpers for Agent1 (LangChain / LangGraph / Studio) installs.
# Dot-source from other scripts in this folder.

$script:Agent1Home = Join-Path $env:LOCALAPPDATA "AlexsoftAgent1"
$script:Agent1Venv = Join-Path $script:Agent1Home "venv"
$script:Agent1Python = Join-Path $script:Agent1Venv "Scripts\python.exe"
$script:Agent1Pip = Join-Path $script:Agent1Venv "Scripts\pip.exe"
$script:LangFlowHome = Join-Path $env:LOCALAPPDATA "LangFlow"
$script:LangFlowVenv = Join-Path $script:LangFlowHome "venv"
$script:LangFlowPython = Join-Path $script:LangFlowVenv "Scripts\python.exe"

function Find-Python312 {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $resolved = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) { return $resolved.Trim() }
    }
    foreach ($name in @("python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -and ($cmd.Source -notmatch '\\WindowsApps\\')) {
            $ver = & $cmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver -and $ver.Trim() -eq "3.12") { return $cmd.Source }
        }
    }
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312"),
        (Join-Path $env:ProgramFiles "Python312")
    )
    foreach ($root in $roots) {
        $candidate = Join-Path $root "python.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Ensure-Agent1Venv {
    New-Item -ItemType Directory -Force -Path $script:Agent1Home | Out-Null
    if (Test-Path $script:Agent1Python) {
        Write-Host "venv already present: $script:Agent1Venv"
        return
    }
    $pythonExe = Find-Python312
    if (-not $pythonExe) {
        Write-Host "Python 3.12 not found. Installing via winget ..."
        & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Error "winget failed to install Python.Python.3.12. Install Python 3.12 manually, then re-run."
        }
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pythonExe = Find-Python312
        if (-not $pythonExe) {
            Write-Error "Python 3.12 still not on PATH after install. Open a new terminal and re-run."
        }
    }
    $verOut = & $pythonExe --version 2>&1
    Write-Host "Using $verOut ($pythonExe)"
    Write-Host "Creating venv: $script:Agent1Venv"
    & $pythonExe -m venv $script:Agent1Venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $script:Agent1Python)) {
        Write-Error "Failed to create venv at $script:Agent1Venv"
    }
}

function Ensure-PipReady {
    Write-Host "Upgrading pip ..."
    & $script:Agent1Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip upgrade failed (continuing with existing pip)."
    }

    # Windows system SOCKS proxy makes pip fail without PySocks (chicken-and-egg).
    $socksOk = $false
    try {
        & $script:Agent1Python -c "import socks" 2>$null
        if ($LASTEXITCODE -eq 0) { $socksOk = $true }
    } catch { }

    if (-not $socksOk) {
        Write-Host "Bootstrapping PySocks via curl (Windows SOCKS proxy) ..."
        $wheels = Join-Path $script:Agent1Home "wheels"
        New-Item -ItemType Directory -Force -Path $wheels | Out-Null
        $whl = Join-Path $wheels "PySocks-1.7.1-py3-none-any.whl"
        $whlUrl = "https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl"
        if (-not (Test-Path $whl)) {
            & curl.exe -L --fail --retry 3 -o $whl $whlUrl
            if ($LASTEXITCODE -ne 0) { Write-Error "Failed to download PySocks wheel" }
        }
        & $script:Agent1Python -m pip install --no-index --find-links $wheels "PySocks==1.7.1"
        if ($LASTEXITCODE -ne 0) { Write-Error "PySocks bootstrap failed" }
    }
}

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-RepoRootMarker {
    param([string]$HomeDir)
    $repoRoot = Get-RepoRoot
    Set-Content -Path (Join-Path $HomeDir "repo-root.txt") -Value $repoRoot -Encoding utf8
}

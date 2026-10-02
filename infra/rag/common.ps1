# Shared helpers for the RAG service (apps/rag). Dot-source from other scripts in this folder.

$script:RagHome = Join-Path $env:LOCALAPPDATA "AlexsoftRag"
$script:RagVenv = Join-Path $script:RagHome "venv"
$script:RagPython = Join-Path $script:RagVenv "Scripts\python.exe"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

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
    foreach ($root in @((Join-Path $env:LOCALAPPDATA "Programs\Python\Python312"), (Join-Path $env:ProgramFiles "Python312"))) {
        $candidate = Join-Path $root "python.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Ensure-RagVenv {
    New-Item -ItemType Directory -Force -Path $script:RagHome | Out-Null
    if (Test-Path $script:RagPython) {
        Write-Host "venv already present: $script:RagVenv"
        return
    }
    $pythonExe = Find-Python312
    if (-not $pythonExe) {
        Write-Host "Python 3.12 not found. Installing via winget ..."
        & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { Write-Error "winget failed to install Python 3.12. Install it manually, then re-run." }
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pythonExe = Find-Python312
        if (-not $pythonExe) { Write-Error "Python 3.12 still not on PATH. Open a new terminal and re-run." }
    }
    Write-Host "Using $(& $pythonExe --version 2>&1) ($pythonExe)"
    & $pythonExe -m venv $script:RagVenv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $script:RagPython)) {
        Write-Error "Failed to create venv at $script:RagVenv"
    }
}

function Ensure-PipReady {
    & $script:RagPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Warning "pip upgrade failed (continuing)." }

    # Windows system SOCKS proxy makes pip fail without PySocks (same workaround as agent1).
    $socksOk = $false
    try {
        & $script:RagPython -c "import socks" 2>$null
        if ($LASTEXITCODE -eq 0) { $socksOk = $true }
    } catch { }
    if (-not $socksOk) {
        Write-Host "Bootstrapping PySocks via curl ..."
        $wheels = Join-Path $script:RagHome "wheels"
        New-Item -ItemType Directory -Force -Path $wheels | Out-Null
        $whl = Join-Path $wheels "PySocks-1.7.1-py3-none-any.whl"
        $whlUrl = "https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl"
        if (-not (Test-Path $whl)) {
            & curl.exe -L --fail --retry 3 -o $whl $whlUrl
            if ($LASTEXITCODE -ne 0) { Write-Error "Failed to download PySocks wheel" }
        }
        & $script:RagPython -m pip install --no-index --find-links $wheels "PySocks==1.7.1"
        if ($LASTEXITCODE -ne 0) { Write-Error "PySocks bootstrap failed" }
    }
}

# Create Python venv + install litellm[proxy] into %LOCALAPPDATA%\LiteLLM.
# Requires Python 3.11+ (winget: Python.Python.3.12).
# powershell -ExecutionPolicy Bypass -File infra\litellm\install-litellm.ps1

$ErrorActionPreference = "Stop"

$litellmHome = Join-Path $env:LOCALAPPDATA "LiteLLM"
$venvDir = Join-Path $litellmHome "venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

function Find-PythonExe {
    foreach ($name in @("python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -and ($cmd.Source -notmatch '\\WindowsApps\\')) {
            return $cmd.Source
        }
    }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $resolved = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) { return $resolved.Trim() }
        $resolved = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) { return $resolved.Trim() }
    }
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        (Join-Path $env:ProgramFiles "Python312"),
        (Join-Path $env:ProgramFiles "Python311")
    ) | Where-Object { $_ -and (Test-Path $_) }
    foreach ($root in $roots) {
        $found = Get-ChildItem -Path $root -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\python\.exe$' -and $_.FullName -notmatch '\\WindowsApps\\' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    return $null
}

New-Item -ItemType Directory -Force -Path $litellmHome | Out-Null

$pythonExe = Find-PythonExe
if (-not $pythonExe) {
    Write-Host "Python not found. Installing Python 3.12 via winget ..."
    & winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Error "winget failed to install Python.Python.3.12. Install Python 3.11+ manually, then re-run."
    }
    # Refresh PATH for this process
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
        [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pythonExe = Find-PythonExe
    if (-not $pythonExe) {
        Write-Error "Python still not on PATH after install. Open a new terminal and re-run install-litellm.ps1."
    }
}

$verOut = & $pythonExe --version 2>&1
Write-Host "Using $verOut ($pythonExe)"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating venv: $venvDir"
    & $pythonExe -m venv $venvDir
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Error "Failed to create venv at $venvDir"
    }
} else {
    Write-Host "venv already present: $venvDir"
}

Write-Host "Upgrading pip ..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Warning "pip upgrade failed (continuing with existing pip)."
}

# Windows system SOCKS proxy makes pip fail without PySocks (chicken-and-egg).
$socksOk = $false
try {
    & $venvPython -c "import socks" 2>$null
    if ($LASTEXITCODE -eq 0) { $socksOk = $true }
} catch { }

if (-not $socksOk) {
    Write-Host "Bootstrapping PySocks via curl (Windows SOCKS proxy) ..."
    $wheels = Join-Path $litellmHome "wheels"
    New-Item -ItemType Directory -Force -Path $wheels | Out-Null
    $whl = Join-Path $wheels "PySocks-1.7.1-py3-none-any.whl"
    $whlUrl = "https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl"
    if (-not (Test-Path $whl)) {
        & curl.exe -L --fail --retry 3 -o $whl $whlUrl
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to download PySocks wheel" }
    }
    & $venvPython -m pip install --no-index --find-links $wheels "PySocks==1.7.1"
    if ($LASTEXITCODE -ne 0) { Write-Error "PySocks bootstrap failed" }
}

Write-Host "Installing litellm[proxy] + prisma (Admin UI DB) ..."
& $venvPip install --upgrade "litellm[proxy]" "prisma>=0.11.0,<1.0"
if ($LASTEXITCODE -ne 0) { Write-Error "litellm[proxy]/prisma install failed" }

# Prisma client engines used by LiteLLM proxy when DATABASE_URL is set.
Write-Host "Fetching Prisma engines (prisma py fetch) ..."
& $venvPython -m prisma py fetch
if ($LASTEXITCODE -ne 0) {
    Write-Warning "prisma py fetch failed; Admin UI DB may need a manual 'python -m prisma py fetch' later."
}

$schema = Join-Path $venvDir "Lib\site-packages\litellm\proxy\schema.prisma"
$prismaExe = Join-Path $venvDir "Scripts\prisma.exe"
if ((Test-Path $schema) -and (Test-Path $prismaExe)) {
    Write-Host "Generating Prisma client ..."
    Push-Location (Split-Path -Parent $schema)
    try {
        & $prismaExe generate
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "prisma generate failed; run infra\litellm\setup-prisma.ps1 later."
        }
    } finally {
        Pop-Location
    }
}

$litellmCli = Join-Path $venvDir "Scripts\litellm.exe"
if (-not (Test-Path $litellmCli)) {
    Write-Error "litellm.exe not found at $litellmCli after install"
}

Write-Host ""
Write-Host "Install dir: $litellmHome"
Write-Host "venv:        $venvDir"
Write-Host "CLI:         $litellmCli"
& $venvPython -c "import litellm; print('litellm', getattr(litellm, '__version__', 'ok'))"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\litellm\start-litellm.ps1"

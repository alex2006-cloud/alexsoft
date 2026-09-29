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

function Get-ProcessTreeIds {
    # Children before parents, so a launcher cannot respawn workers while we kill them.
    param([Parameter(Mandatory = $true)][int]$RootProcessId)

    $all = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId -ErrorAction SilentlyContinue)
    $ordered = New-Object System.Collections.Generic.List[int]
    $pending = New-Object System.Collections.Generic.Queue[int]
    $pending.Enqueue($RootProcessId)

    while ($pending.Count -gt 0) {
        $current = $pending.Dequeue()
        if ($ordered.Contains($current)) { continue }
        $ordered.Add($current)
        foreach ($child in ($all | Where-Object {
                    [int]$_.ParentProcessId -eq $current -and [int]$_.ProcessId -ne $current
                })) {
            $pending.Enqueue([int]$child.ProcessId)
        }
    }

    $ordered.Reverse()
    return $ordered.ToArray()
}

function Test-Agent1Process {
    # Guards against a stale pid file or a reused PID pointing at something unrelated.
    param([Parameter(Mandatory = $true)][int]$ProcessId)

    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $proc) { return $false }
    if ($proc.CommandLine -and $proc.CommandLine -like "*$script:Agent1Home*") { return $true }

    # Spawned workers only show a generic command line; their loaded .pyd files give them away.
    try {
        foreach ($m in (Get-Process -Id $ProcessId -ErrorAction Stop).Modules) {
            if ($m.FileName -and $m.FileName.StartsWith($script:Agent1Venv, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
    } catch { }
    return $false
}

function Get-Agent1OrphanWorkerIds {
    # Agent Server workers keep the inherited listening socket after their launcher is gone.
    $all = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, CommandLine -ErrorAction SilentlyContinue)
    $livePids = @{}
    foreach ($p in $all) { $livePids[[int]$p.ProcessId] = $true }

    $orphans = @()
    foreach ($p in $all) {
        if ($p.Name -notmatch '^pythonw?\.exe$') { continue }
        if (-not $p.CommandLine -or $p.CommandLine -notmatch 'multiprocessing') { continue }
        if ($livePids.ContainsKey([int]$p.ParentProcessId)) { continue }
        if (-not (Test-Agent1Process -ProcessId ([int]$p.ProcessId))) { continue }
        $orphans += [int]$p.ProcessId
    }
    return $orphans
}

function Test-Agent1PortBusy {
    param([int]$Port = 2024)

    foreach ($path in @("ok", "docs")) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/$path" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { return $true }
        } catch { }
    }

    # A Listen entry can outlive its owner; only a live owner means the port is really taken.
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn -and (Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue)) { return $true }
    return $false
}

function Stop-Agent1Studio {
    param([int]$Port = 2024)

    $pidFile = Join-Path $script:Agent1Home "studio.pid"
    $roots = @()

    if (Test-Path $pidFile) {
        $recorded = 0
        if ([int]::TryParse((Get-Content $pidFile -Raw).Trim(), [ref]$recorded) -and $recorded -gt 0) {
            $roots += $recorded
        }
    }
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { $roots += [int]$_.OwningProcess }

    foreach ($root in ($roots | Sort-Object -Unique)) {
        if (-not (Test-Agent1Process -ProcessId $root)) { continue }
        foreach ($procId in (Get-ProcessTreeIds -RootProcessId $root)) {
            if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped PID $procId"
            }
        }
    }

    foreach ($procId in (Get-Agent1OrphanWorkerIds)) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped orphaned Agent Server worker PID $procId"
    }

    if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }

    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-Agent1PortBusy -Port $Port)) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (-not (Test-Agent1PortBusy -Port $Port))
}

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-RepoRootMarker {
    param([string]$HomeDir)
    $repoRoot = Get-RepoRoot
    Set-Content -Path (Join-Path $HomeDir "repo-root.txt") -Value $repoRoot -Encoding utf8
}

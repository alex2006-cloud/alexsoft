# Stop the RAG service started by start-rag.ps1.
# powershell -ExecutionPolicy Bypass -File infra\rag\stop-rag.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$envFile = Join-Path (Get-RepoRoot) ".env"
$port = [int](Read-DotEnvValue -Path $envFile -Key "RAG_PORT" -Default "8200")
$pidFile = Join-Path $script:RagHome "rag.pid"

$ids = @()
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { $ids += [int]$_.OwningProcess }
if (Test-Path $pidFile) {
    $recorded = 0
    if ([int]::TryParse((Get-Content $pidFile -Raw).Trim(), [ref]$recorded) -and $recorded -gt 0) { $ids += $recorded }
}

$stopped = $false
foreach ($procId in ($ids | Sort-Object -Unique)) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue
    # Only stop processes that run from the RAG venv
    if ($p -and $p.ExecutablePath -and $p.ExecutablePath.StartsWith($script:RagVenv, [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped PID $procId"
        $stopped = $true
    }
}
if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
if (-not $stopped) { Write-Host "RAG is not running." } else { Write-Host "RAG stopped." }

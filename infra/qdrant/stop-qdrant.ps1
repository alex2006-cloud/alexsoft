# Stop local Qdrant started by start-qdrant.ps1.
# powershell -ExecutionPolicy Bypass -File infra\qdrant\stop-qdrant.ps1

$ErrorActionPreference = "Stop"

$ids = @(Get-NetTCPConnection -LocalPort 6333, 6334 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique)

if (-not $ids) {
    $byName = Get-Process -Name qdrant -ErrorAction SilentlyContinue
    if (-not $byName) {
        Write-Host "Qdrant is not running."
        exit 0
    }
    $ids = @($byName.Id)
}

foreach ($procId in $ids) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $procId"
}

Start-Sleep -Milliseconds 500
Write-Host "Qdrant stopped."

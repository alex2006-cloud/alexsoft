# Stop local MinIO started by start-minio.ps1.
# powershell -ExecutionPolicy Bypass -File infra\minio\stop-minio.ps1

$ErrorActionPreference = "Stop"

$listeners = Get-NetTCPConnection -LocalPort 9000, 9001 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $listeners) {
    $byName = Get-Process -Name minio -ErrorAction SilentlyContinue
    if (-not $byName) {
        Write-Host "MinIO is not running."
        exit 0
    }
    $listeners = $byName.Id
}

foreach ($procId in $listeners) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID $procId"
}

Start-Sleep -Milliseconds 500
Write-Host "MinIO stopped."

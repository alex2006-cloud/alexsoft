# Stop the local gateway nginx started by start-nginx.ps1.
# powershell -ExecutionPolicy Bypass -File infra\nginx\local\stop-nginx.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$stopped = $false
# Only nginx processes that run from our install dir
Get-CimInstance Win32_Process -Filter "Name = 'nginx.exe'" -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($script:NginxHome, [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $stopped = $true
    }
}
if ($stopped) { Write-Host "nginx stopped." } else { Write-Host "nginx is not running." }

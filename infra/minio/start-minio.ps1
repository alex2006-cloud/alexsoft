# Start local MinIO (S3 API :9000, Console :9001). See README.md.
# powershell -ExecutionPolicy Bypass -File infra\minio\start-minio.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$minioHome = Join-Path $env:LOCALAPPDATA "MinIO"
$minioExe = Join-Path $minioHome "minio.exe"
$dataDir = Join-Path $minioHome "data"
$logFile = Join-Path $minioHome "minio.log"
$errFile = Join-Path $minioHome "minio.err.log"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key=(.*)$") {
            return $Matches[1].Trim()
        }
    }
    return $Default
}

if (-not (Test-Path $minioExe)) {
    Write-Error "minio.exe not found at $minioExe. Run install-minio.ps1 first."
}

$listen = Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "MinIO already listening on 127.0.0.1:9000 (PID $($listen.OwningProcess))"
    Write-Host "Console: http://127.0.0.1:9001"
    exit 0
}

$user = Read-DotEnvValue -Path $envFile -Key "MINIO_ROOT_USER" -Default "minioadmin"
$password = Read-DotEnvValue -Path $envFile -Key "MINIO_ROOT_PASSWORD" -Default "change-me"
$apiPort = Read-DotEnvValue -Path $envFile -Key "MINIO_PORT" -Default "9000"
$consolePort = Read-DotEnvValue -Path $envFile -Key "MINIO_CONSOLE_PORT" -Default "9001"

if ($password.Length -lt 8) {
    Write-Error "MINIO_ROOT_PASSWORD must be at least 8 characters (MinIO requirement)."
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

$env:MINIO_ROOT_USER = $user
$env:MINIO_ROOT_PASSWORD = $password
$env:MINIO_UPDATE = "off"
$env:MINIO_BROWSER_REDIRECT_URL = "http://127.0.0.1:$consolePort"

$args = @(
    "server", $dataDir,
    "--address", "127.0.0.1:$apiPort",
    "--console-address", "127.0.0.1:$consolePort"
)

$proc = Start-Process -FilePath $minioExe -ArgumentList $args -WorkingDirectory $minioHome `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru

Start-Sleep -Seconds 2

$up = Get-NetTCPConnection -LocalPort ([int]$apiPort) -State Listen -ErrorAction SilentlyContinue
if (-not $up) {
    Write-Error "MinIO did not start. See $logFile"
}

Write-Host "MinIO started (PID $($proc.Id))"
Write-Host "S3 API:  http://127.0.0.1:$apiPort"
Write-Host "Console: http://127.0.0.1:$consolePort"
Write-Host "User:    $user"
Write-Host "Log:     $logFile"

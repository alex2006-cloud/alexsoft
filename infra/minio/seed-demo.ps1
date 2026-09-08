# Create bucket and upload demo objects. MinIO must be running.
# powershell -ExecutionPolicy Bypass -File infra\minio\seed-demo.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"
$objectsDir = Join-Path $scriptDir "demo\objects"
$minioHome = Join-Path $env:LOCALAPPDATA "MinIO"
$mcExe = Join-Path $minioHome "mc.exe"
$aliasName = "alexsoft"

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

if (-not (Test-Path $mcExe)) {
    Write-Error "mc.exe not found at $mcExe. Run install-minio.ps1 first."
}
if (-not (Test-Path $objectsDir)) {
    Write-Error "Demo objects not found: $objectsDir"
}

$user = Read-DotEnvValue -Path $envFile -Key "MINIO_ROOT_USER" -Default "minioadmin"
$password = Read-DotEnvValue -Path $envFile -Key "MINIO_ROOT_PASSWORD" -Default "change-me"
$endpoint = Read-DotEnvValue -Path $envFile -Key "MINIO_ENDPOINT" -Default "localhost"
$apiPort = Read-DotEnvValue -Path $envFile -Key "MINIO_PORT" -Default "9000"
$bucket = Read-DotEnvValue -Path $envFile -Key "MINIO_BUCKET" -Default "alexsoft"

$apiUrl = "http://${endpoint}:${apiPort}"

& $mcExe alias set $aliasName $apiUrl $user $password --api S3v4 | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Error "mc alias set failed" }

& $mcExe mb --ignore-existing "$aliasName/$bucket" | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Error "mc mb failed" }

& $mcExe mirror --overwrite $objectsDir "$aliasName/$bucket/demo" | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Error "mc mirror failed" }

Write-Host ""
Write-Host "Bucket: $bucket"
Write-Host "Prefix: demo/"
& $mcExe ls --recursive "$aliasName/$bucket/demo" | Out-Host
Write-Host ""
Write-Host "Console: http://127.0.0.1:$(Read-DotEnvValue -Path $envFile -Key "MINIO_CONSOLE_PORT" -Default "9001")"

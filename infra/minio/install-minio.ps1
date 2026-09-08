# Download minio.exe and mc.exe into %LOCALAPPDATA%\MinIO.
# powershell -ExecutionPolicy Bypass -File infra\minio\install-minio.ps1

$ErrorActionPreference = "Stop"

$minioHome = Join-Path $env:LOCALAPPDATA "MinIO"
New-Item -ItemType Directory -Force -Path $minioHome | Out-Null

$minioUrl = "https://dl.min.io/server/minio/release/windows-amd64/minio.exe"
$mcUrl = "https://dl.min.io/client/mc/release/windows-amd64/mc.exe"
$minioExe = Join-Path $minioHome "minio.exe"
$mcExe = Join-Path $minioHome "mc.exe"

function Get-Binary {
    param([string]$Url, [string]$OutFile, [string]$Label)
    if (Test-Path $OutFile) {
        Write-Host "$Label already present: $OutFile"
        return
    }
    Write-Host "Downloading $Label ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $OutFile $Url
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $OutFile)) {
        Write-Error "Failed to download $Label from $Url"
    }
    Write-Host "Saved $Label -> $OutFile"
}

Get-Binary -Url $minioUrl -OutFile $minioExe -Label "minio.exe"
Get-Binary -Url $mcUrl -OutFile $mcExe -Label "mc.exe"

Write-Host ""
Write-Host "Install dir: $minioHome"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\minio\start-minio.ps1"

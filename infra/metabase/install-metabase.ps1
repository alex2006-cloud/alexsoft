# Download Metabase OSS JAR into %LOCALAPPDATA%\Metabase.
# Requires Java 25+ (Eclipse Temurin JRE recommended).
# powershell -ExecutionPolicy Bypass -File infra\metabase\install-metabase.ps1

$ErrorActionPreference = "Stop"

# Pin 0.63.17+: 0.63.16.x crashes on Windows JAR path ("Illegal char <:>" /C:/...).
$metabaseVersion = "0.63.17"
$metabaseHome = Join-Path $env:LOCALAPPDATA "Metabase"
$jarPath = Join-Path $metabaseHome "metabase.jar"
$downloadUrl = "https://downloads.metabase.com/v$metabaseVersion.x/metabase.jar"

New-Item -ItemType Directory -Force -Path $metabaseHome | Out-Null

if (Test-Path $jarPath) {
    $sizeMb = [math]::Round((Get-Item $jarPath).Length / 1MB, 1)
    Write-Host "metabase.jar already present: $jarPath ($sizeMb MB)"
} else {
    Write-Host "Downloading Metabase OSS v$metabaseVersion (~500 MB) ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $jarPath $downloadUrl
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $jarPath)) {
        if (Test-Path $jarPath) { Remove-Item -Force $jarPath }
        Write-Error "Failed to download Metabase from $downloadUrl"
    }
    $sizeMb = [math]::Round((Get-Item $jarPath).Length / 1MB, 1)
    Write-Host "Saved metabase.jar -> $jarPath ($sizeMb MB)"
}

Write-Host ""
Write-Host "Install dir: $metabaseHome"
Write-Host "JAR:         $jarPath"
Write-Host "Version:     $metabaseVersion"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\metabase\start-metabase.ps1"

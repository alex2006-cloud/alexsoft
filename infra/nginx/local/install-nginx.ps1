# Download the official nginx for Windows (zip from nginx.org) into %LOCALAPPDATA%\AlexsoftNginx.
# powershell -ExecutionPolicy Bypass -File infra\nginx\local\install-nginx.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

if (Test-Path $script:NginxExe) {
    Write-Host "nginx already installed: $script:NginxDir"
    & $script:NginxExe -v
    exit 0
}

New-Item -ItemType Directory -Force -Path $script:NginxHome | Out-Null
$zip = Join-Path $script:NginxHome ("nginx-" + $script:NginxVersion + ".zip")
$url = "https://nginx.org/download/nginx-" + $script:NginxVersion + ".zip"
Write-Host "Downloading $url ..."
& curl.exe -L --fail --retry 3 -o $zip $url
if ($LASTEXITCODE -ne 0) { Write-Error "Download failed: $url" }

Expand-Archive -Path $zip -DestinationPath $script:NginxHome -Force
Remove-Item $zip -Force
if (-not (Test-Path $script:NginxExe)) { Write-Error "nginx.exe not found after unzip: $script:NginxExe" }
New-Item -ItemType Directory -Force -Path (Join-Path $script:NginxDir "logs") | Out-Null

& $script:NginxExe -v
Write-Host "OK  installed to $script:NginxDir"
Write-Host "Next: infra\nginx\local\start-nginx.ps1"

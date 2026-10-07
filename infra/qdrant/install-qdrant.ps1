# Download qdrant.exe + Web UI into %LOCALAPPDATA%\Qdrant (native Windows, ADR-0017).
# The Windows binary does not bundle /dashboard — Web UI is a separate release (static/).
# powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1
# powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1 -Version v1.15.5
# powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1 -ForceWebUi

param(
    [string]$Version = "latest",
    [string]$WebUiVersion = "latest",
    [switch]$ForceWebUi
)

$ErrorActionPreference = "Stop"

$qdrantHome = Join-Path $env:LOCALAPPDATA "Qdrant"
$qdrantExe = Join-Path $qdrantHome "qdrant.exe"
$staticDir = Join-Path $qdrantHome "static"
New-Item -ItemType Directory -Force -Path $qdrantHome | Out-Null

function Install-QdrantBinary {
    if ((Test-Path $qdrantExe) -and -not $ForceWebUi) {
        # ForceWebUi alone must not re-download the binary; only -Version forces a refresh if missing
    }
    if (Test-Path $qdrantExe) {
        Write-Host "qdrant.exe already present: $qdrantExe"
        & $qdrantExe --version
        return
    }

    $asset = "qdrant-x86_64-pc-windows-msvc.zip"
    $url = if ($Version -eq "latest") {
        "https://github.com/qdrant/qdrant/releases/latest/download/$asset"
    } else {
        "https://github.com/qdrant/qdrant/releases/download/$Version/$asset"
    }

    $zip = Join-Path $env:TEMP $asset
    Write-Host "Downloading $url ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zip $url
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zip)) {
        Write-Error "Failed to download $url"
    }

    Expand-Archive -Path $zip -DestinationPath $qdrantHome -Force
    Remove-Item $zip -Force -ErrorAction SilentlyContinue

    if (-not (Test-Path $qdrantExe)) {
        Write-Error "qdrant.exe not found after unzip in $qdrantHome"
    }

    Write-Host "Saved -> $qdrantExe"
    & $qdrantExe --version
}

function Install-QdrantWebUi {
    $index = Join-Path $staticDir "index.html"
    if ((Test-Path $index) -and -not $ForceWebUi) {
        Write-Host "Web UI already present: $staticDir"
        return
    }

    $asset = "dist-qdrant.zip"
    $url = if ($WebUiVersion -eq "latest") {
        "https://github.com/qdrant/qdrant-web-ui/releases/latest/download/$asset"
    } else {
        "https://github.com/qdrant/qdrant-web-ui/releases/download/$WebUiVersion/$asset"
    }

    $zip = Join-Path $env:TEMP $asset
    $extract = Join-Path $env:TEMP "qdrant-web-ui-extract"
    Write-Host "Downloading Web UI $url ..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $zip $url
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $zip)) {
        Write-Error "Failed to download $url"
    }

    if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $extract -Force
    Remove-Item $zip -Force -ErrorAction SilentlyContinue

    $found = Get-ChildItem -Path $extract -Recurse -Filter index.html | Select-Object -First 1
    if (-not $found) {
        Write-Error "index.html not found in Web UI archive"
    }
    $src = $found.Directory.FullName

    if (Test-Path $staticDir) { Remove-Item $staticDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $staticDir | Out-Null
    Copy-Item -Path (Join-Path $src "*") -Destination $staticDir -Recurse -Force
    Remove-Item $extract -Recurse -Force -ErrorAction SilentlyContinue

    if (-not (Test-Path $index)) {
        Write-Error "Web UI install failed: $index missing"
    }
    Write-Host "Web UI saved -> $staticDir"
    Write-Host "Restart Qdrant to pick it up: infra\qdrant\stop-qdrant.ps1 ; infra\qdrant\start-qdrant.ps1"
}

Install-QdrantBinary
Install-QdrantWebUi

Write-Host ""
Write-Host "Next: powershell -ExecutionPolicy Bypass -File infra\qdrant\start-qdrant.ps1"
Write-Host "Dashboard: http://127.0.0.1:6333/dashboard"

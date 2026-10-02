# Start the RAG service (FastAPI, apps/rag) on RAG_PORT (default 8200).
# Requires: Qdrant (infra\qdrant), PostgreSQL, MinIO, LiteLLM running.
# powershell -ExecutionPolicy Bypass -File infra\rag\start-rag.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$envFile = Join-Path (Get-RepoRoot) ".env"
$port = [int](Read-DotEnvValue -Path $envFile -Key "RAG_PORT" -Default "8200")
$logFile = Join-Path $script:RagHome "rag.out.log"
$errFile = Join-Path $script:RagHome "rag.err.log"
$pidFile = Join-Path $script:RagHome "rag.pid"

if (-not (Test-Path $script:RagPython)) {
    Write-Error "venv not found at $script:RagVenv. Run install-rag.ps1 first."
}

$listen = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listen) {
    Write-Host "RAG already listening on 127.0.0.1:$port (PID $($listen[0].OwningProcess)). Run stop-rag.ps1 to restart."
    exit 0
}

# Keep model caches outside the repo
$env:TIKTOKEN_CACHE_DIR = Join-Path $script:RagHome "tiktoken"
New-Item -ItemType Directory -Force -Path $env:TIKTOKEN_CACHE_DIR | Out-Null
# Local services must not go through a system proxy
$env:NO_PROXY = "127.0.0.1,localhost"

$proc = Start-Process -FilePath $script:RagPython -ArgumentList @("-m", "alexsoft_rag") `
    -WorkingDirectory (Join-Path (Get-RepoRoot) "apps\rag") `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -WindowStyle Hidden -PassThru
Set-Content -Path $pidFile -Value $proc.Id

# First start downloads the BM25 model (needs internet) - allow time
$deadline = (Get-Date).AddSeconds(90)
$ok = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { break }
    # curl.exe, not Invoke-WebRequest: the latter goes through the Windows system proxy
    $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 2 "http://127.0.0.1:$port/health/live"
    if ($code -eq "200") { $ok = $true; break }
}
if (-not $ok) {
    Write-Host (Get-Content $errFile -Tail 25 -ErrorAction SilentlyContinue | Out-String)
    Write-Error "RAG did not start. See $errFile"
}

Write-Host "RAG started (PID $($proc.Id))"
Write-Host "API:    http://127.0.0.1:$port   (docs: /docs)"
Write-Host "Ready:  curl.exe http://127.0.0.1:$port/health/ready"
Write-Host "Log:    $errFile"

# Phase 7: stop local Windows product runtime after VDS cutover.
# Leaves Cursor + git. Does not uninstall binaries / wipe data dirs.
# Run from repo root: powershell -ExecutionPolicy Bypass -File infra\stop-local-product-runtime.ps1

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot

function Invoke-StopScript([string]$rel) {
  $p = Join-Path $root $rel
  if (Test-Path $p) {
    Write-Host "==> $rel"
    & powershell -ExecutionPolicy Bypass -File $p
  } else {
    Write-Host "-- skip missing $rel"
  }
}

$scripts = @(
  "infra\api\stop-api.ps1",
  "infra\rag\stop-rag.ps1",
  "infra\litellm\stop-litellm.ps1",
  "infra\agent1\stop-studio.ps1",
  "infra\agent1\stop-langflow.ps1",
  "infra\authentik\stop-authentik.ps1",
  "infra\metabase\stop-metabase.ps1",
  "infra\grafana\stop-grafana.ps1",
  "infra\alloy\stop-alloy.ps1",
  "infra\prometheus\stop-prometheus.ps1",
  "infra\loki\stop-loki.ps1",
  "infra\minio\stop-minio.ps1",
  "infra\qdrant\stop-qdrant.ps1",
  "infra\n8n\stop-n8n.ps1",
  "infra\dify\stop-dify.ps1",
  "infra\nginx\local\stop-nginx.ps1"
)

foreach ($s in $scripts) { Invoke-StopScript $s }

$memuraiStop = Join-Path $env:LOCALAPPDATA "Memurai\stop-memurai.ps1"
if (Test-Path $memuraiStop) {
  Write-Host "==> Memurai stop"
  & powershell -ExecutionPolicy Bypass -File $memuraiStop
}

# PostgreSQL Windows service — stop + Manual (needs elevation)
$pg = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($pg) {
  Write-Host "==> PostgreSQL service Stop + Manual (may prompt UAC)"
  $cmd = "Stop-Service -Name postgresql-x64-16 -Force -ErrorAction SilentlyContinue; Set-Service -Name postgresql-x64-16 -StartupType Manual -ErrorAction SilentlyContinue"
  try {
    if ($pg.Status -eq "Running") { Stop-Service -Name $pg.Name -Force -ErrorAction Stop }
    Set-Service -Name $pg.Name -StartupType Manual -ErrorAction Stop
  } catch {
    Start-Process -FilePath "powershell.exe" -Verb RunAs -Wait -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `$ErrorActionPreference='Stop'; $cmd"
  }
}

Write-Host ""
Write-Host "Listening product ports (expect empty):"
netstat -ano | findstr "LISTENING" | findstr ":5432 :6379 :9000 :6333 :5672 :8080 :8100 :8200 :2024 :3001 :3002 :9100 :4000"
Write-Host "OK: local product runtime stopped (Cursor + git remain)."

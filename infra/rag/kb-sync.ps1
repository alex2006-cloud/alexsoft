# Sync the repo into the project knowledge base (Qdrant collections project-docs / project-code).
# Incremental: unchanged files (by sha256) are skipped; vanished files are removed from the index.
# Needs running: Qdrant, MinIO, PostgreSQL, LiteLLM (OPENAI_API_KEY for embeddings, DEEPSEEK_API_KEY for summaries), RAG.
#
#   powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -DryRun        # what would be synced
#   powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1                # full sync
#   powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -NoSummaries   # without LLM summaries
#   powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -Only "apps/rag/**" -Force

param(
    [switch]$DryRun,
    [switch]$NoSummaries,
    [switch]$Force,
    [switch]$Strict,
    [switch]$VerboseSkips,
    [string[]]$Only = @(),
    [string[]]$Collection = @()
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$env:NO_PROXY = "127.0.0.1,localhost"
$env:TIKTOKEN_CACHE_DIR = Join-Path $script:RagHome "tiktoken"
$argsList = @("-m", "alexsoft_rag.kbsync")
if ($DryRun) { $argsList += "--dry-run" }
if ($NoSummaries) { $argsList += "--no-summaries" }
if ($Force) { $argsList += "--force" }
if ($Strict) { $argsList += "--strict" }
if ($VerboseSkips) { $argsList += "-v" }
foreach ($o in $Only) { $argsList += @("--only", $o) }
foreach ($c in $Collection) { $argsList += @("--collection", $c) }

Push-Location (Join-Path (Get-RepoRoot) "apps\rag")
try {
    & $script:RagPython @argsList
    if ($LASTEXITCODE -ne 0) { Write-Error "kb-sync failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

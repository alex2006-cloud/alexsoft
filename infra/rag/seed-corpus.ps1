# Upload project docs to MinIO (rag-docs) and ingest them into Qdrant via the RAG API.
# Needs running: Qdrant, MinIO, PostgreSQL, LiteLLM (with OPENAI_API_KEY for embeddings), RAG (start-rag.ps1).
# powershell -ExecutionPolicy Bypass -File infra\rag\seed-corpus.ps1 [-DryRun]

param([switch]$DryRun)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$env:NO_PROXY = "127.0.0.1,localhost"
$argsList = @((Join-Path $PSScriptRoot "seed_corpus.py"))
if ($DryRun) { $argsList += "--dry-run" }
& $script:RagPython @argsList
if ($LASTEXITCODE -ne 0) { Write-Error "seed_corpus.py failed (exit $LASTEXITCODE)" }

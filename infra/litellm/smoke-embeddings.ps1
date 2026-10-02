# One embeddings request through local LiteLLM (model text-embedding-3-small, ADR-0017).
# powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-embeddings.ps1

param(
    [string]$Model = "text-embedding-3-small"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$envFile = Join-Path $repoRoot ".env"

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $Default
}

$port = Read-DotEnvValue -Path $envFile -Key "LITELLM_PORT" -Default "8080"
$masterKey = Read-DotEnvValue -Path $envFile -Key "LITELLM_MASTER_KEY" -Default ""
$openai = Read-DotEnvValue -Path $envFile -Key "OPENAI_API_KEY" -Default ""
if (-not $openai) {
    Write-Error "OPENAI_API_KEY is empty in .env. Add it, restart LiteLLM (start-litellm.ps1), re-run."
}

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if (-not $listen) {
    Write-Error "LiteLLM is not listening on port $port. Run start-litellm.ps1 first."
}

$bodyFile = Join-Path $env:TEMP "litellm-embed-body.json"
$outFile = Join-Path $env:TEMP "litellm-embed.json"
Set-Content -Path $bodyFile -Value "{`"model`":`"$Model`",`"input`":[`"hello rag`"]}" -Encoding ascii

$curlArgs = @(
    "-s", "-o", $outFile, "-w", "%{http_code}",
    "http://127.0.0.1:$port/v1/embeddings",
    "-H", "Content-Type: application/json",
    "--data-binary", "@$bodyFile"
)
if ($masterKey) { $curlArgs += @("-H", "Authorization: Bearer $masterKey") }

$httpCode = & curl.exe @curlArgs
if ($LASTEXITCODE -ne 0) { Write-Error "curl failed (exit $LASTEXITCODE)" }

$raw = Get-Content -Raw -Path $outFile
if ($httpCode -ne "200") {
    $safe = [regex]::Replace($raw, 'sk-[A-Za-z0-9_-]{8,}', 'sk-REDACTED')
    Write-Host $safe.Substring(0, [Math]::Min(500, $safe.Length))
    Write-Error "HTTP $httpCode. Response saved to $outFile (check OPENAI_API_KEY / model alias)."
}

$json = $raw | ConvertFrom-Json
$dims = $json.data[0].embedding.Count
Write-Host "Smoke OK (HTTP $httpCode). Model $Model returned $dims dimensions."
if ($dims -ne 1536) { Write-Warning "Expected 1536 dimensions for text-embedding-3-small." }

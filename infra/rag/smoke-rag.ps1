# End-to-end smoke of the running RAG service: collection -> ingest -> search -> query -> cleanup.
# Needs LiteLLM with embeddings (OPENAI_API_KEY) and a chat model (deepseek) running.
# powershell -ExecutionPolicy Bypass -File infra\rag\smoke-rag.ps1 [-SkipQuery]

param([switch]$SkipQuery)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$envFile = Join-Path (Get-RepoRoot) ".env"
$port = Read-DotEnvValue -Path $envFile -Key "RAG_PORT" -Default "8200"
$apiKey = Read-DotEnvValue -Path $envFile -Key "RAG_API_KEY" -Default ""
$base = "http://127.0.0.1:$port"
$name = "smoke-" + [guid]::NewGuid().ToString("N").Substring(0, 8)

function Invoke-Rag {
    param([string]$Method, [string]$Path, $Body = $null)
    $tmp = Join-Path $env:TEMP "rag-smoke-body.json"
    $curlArgs = @("-s", "-X", $Method, "-H", "X-API-Key: $apiKey", "-H", "Content-Type: application/json",
        "-w", "`n%{http_code}", "$base$Path")
    if ($null -ne $Body) {
        Set-Content -Path $tmp -Value ($Body | ConvertTo-Json -Depth 8 -Compress) -Encoding utf8
        $curlArgs += @("--data-binary", "@$tmp")
    }
    $raw = & curl.exe @curlArgs
    $lines = @($raw)
    $code = [int]$lines[-1]
    $text = ($lines[0..($lines.Count - 2)] -join "`n")
    return [pscustomobject]@{ Code = $code; Json = $(if ($text) { $text | ConvertFrom-Json } else { $null }) }
}

function Assert-Code($r, [int]$expected, [string]$what) {
    if ($r.Code -ne $expected) {
        Write-Error "$what -> HTTP $($r.Code) (expected $expected): $($r.Json | ConvertTo-Json -Compress)"
    }
    Write-Host "OK  $what (HTTP $($r.Code))"
}

$ready = & curl.exe -s "$base/health/ready"
Write-Host "ready: $ready"

try {
    Assert-Code (Invoke-Rag POST "/v1/collections" @{ name = $name }) 201 "create collection $name"
    $job = Invoke-Rag POST "/v1/collections/$name/documents" @{
        external_id = "smoke-note"
        source = @{ type = "inline"; content_type = "text/markdown"
            text = "# Брокер`n`nRabbitMQ - целевой брокер сообщений для долгих AI-задач, этап 6." }
        metadata = @{ kind = "note" }
    }
    Assert-Code $job 202 "ingest document"

    $deadline = (Get-Date).AddSeconds(60)
    do {
        Start-Sleep -Milliseconds 500
        $st = (Invoke-Rag GET "/v1/jobs/$($job.Json.id)").Json
    } while ($st.status -in @("queued", "running") -and (Get-Date) -lt $deadline)
    if ($st.status -ne "succeeded") { Write-Error "ingest job $($st.status): $($st.error)" }
    Write-Host "OK  job succeeded"

    $s = Invoke-Rag POST "/v1/search" @{ collection = $name; query = "какой брокер выбран?"; top_k = 3 }
    Assert-Code $s 200 "search"
    if ($s.Json.chunks.Count -lt 1 -or $s.Json.chunks[0].external_id -ne "smoke-note") { Write-Error "search returned no expected chunk" }
    Write-Host "    top chunk score=$($s.Json.chunks[0].score)"

    if (-not $SkipQuery) {
        $q = Invoke-Rag POST "/v1/query" @{ collection = $name; question = "Какой брокер выбран и когда он нужен?" }
        Assert-Code $q 200 "query"
        Write-Host "    answer: $($q.Json.answer)"
        Write-Host "    citations: $($q.Json.citations.Count), insufficient_context=$($q.Json.insufficient_context)"
    }
}
finally {
    $d = Invoke-Rag DELETE "/v1/collections/$name"
    Write-Host "cleanup: DELETE collection -> HTTP $($d.Code)"
}
Write-Host "RAG smoke OK."

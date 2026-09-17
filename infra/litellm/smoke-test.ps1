# One chat completion through local LiteLLM. Default model: deepseek.
# powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-test.ps1
# powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-test.ps1 -Model qwen

param(
    [ValidateSet("deepseek", "qwen")]
    [string]$Model = "deepseek"
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

$keyName = if ($Model -eq "qwen") { "DASHSCOPE_API_KEY" } else { "DEEPSEEK_API_KEY" }
$apiKey = Read-DotEnvValue -Path $envFile -Key $keyName -Default ""
if (-not $apiKey) {
    Write-Error "$keyName is empty in .env. Add the key for model '$Model', restart LiteLLM, re-run this script."
}

$listen = Get-NetTCPConnection -LocalPort ([int]$port) -State Listen -ErrorAction SilentlyContinue
if (-not $listen) {
    Write-Error "LiteLLM is not listening on port $port. Run start-litellm.ps1 first."
}

$bodyFile = Join-Path $env:TEMP "litellm-smoke-body.json"
$outFile = Join-Path $env:TEMP "litellm-smoke.json"
Set-Content -Path $bodyFile -Value "{`"model`":`"$Model`",`"messages`":[{`"role`":`"user`",`"content`":`"Say hi in one word`"}]}" -Encoding ascii

$curlArgs = @(
    "-s", "-o", $outFile, "-w", "%{http_code}",
    "http://127.0.0.1:$port/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "--data-binary", "@$bodyFile"
)
if ($masterKey) {
    $curlArgs += @("-H", "Authorization: Bearer $masterKey")
}

$httpCode = & curl.exe @curlArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "curl failed (exit $LASTEXITCODE)"
}

$raw = Get-Content -Raw -Path $outFile
if ($httpCode -ne "200") {
    $safe = [regex]::Replace($raw, 'sk-[A-Za-z0-9_-]{8,}', 'sk-REDACTED')
    Write-Host $safe.Substring(0, [Math]::Min(500, $safe.Length))
    Write-Error "HTTP $httpCode. Response saved to $outFile (check key / provider)."
}
if ($raw -notmatch '"content"\s*:') {
    Write-Error "Unexpected response (no content). Saved to $outFile"
}

Write-Host "Smoke OK (HTTP $httpCode). Model $Model answered via LiteLLM."
Write-Host "Full JSON: $outFile"

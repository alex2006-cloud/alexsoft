# Start LangGraph Agent Server (Studio backend) on 127.0.0.1:2024
# powershell -ExecutionPolicy Bypass -File infra\agent1\start-studio.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$cli = Join-Path $script:Agent1Venv "Scripts\langgraph.exe"
if (-not (Test-Path $cli)) {
    Write-Error "langgraph CLI missing. Run install-studio.ps1 first."
}

$repoRoot = Get-RepoRoot
$appDir = Join-Path $repoRoot "apps\agent1"
$config = Join-Path $appDir "langgraph.json"
if (-not (Test-Path $config)) {
    Write-Error "Missing $config"
}

# Load selected keys from repo .env into this process
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { return }
        $k, $v = $line.Split("=", 2)
        $k = $k.Trim()
        $v = $v.Trim().Trim('"').Trim("'")
        if ($k -in @(
                "LANGSMITH_API_KEY", "LANGSMITH_TRACING",
                "AI_GATEWAY_URL", "LITELLM_MASTER_KEY", "AGENT1_MODEL",
                "OPENAI_API_KEY", "OPENAI_BASE_URL"
            )) {
            Set-Item -Path "Env:$k" -Value $v
        }
    }
}

if (-not $env:LANGSMITH_TRACING) { $env:LANGSMITH_TRACING = "false" }
# Windows console without colorama used to crash; keep colors off when headless.
if (-not $env:LOG_COLOR) { $env:LOG_COLOR = "false" }

# Map LiteLLM for OpenAI-compatible clients (used after wire step)
if ($env:AI_GATEWAY_URL -and -not $env:OPENAI_BASE_URL) {
    $base = $env:AI_GATEWAY_URL.TrimEnd("/")
    $env:OPENAI_BASE_URL = "$base/v1"
}
if ($env:LITELLM_MASTER_KEY -and -not $env:OPENAI_API_KEY) {
    $env:OPENAI_API_KEY = $env:LITELLM_MASTER_KEY
}

$port = 2024
if ($env:AGENT1_STUDIO_PORT) { $port = [int]$env:AGENT1_STUDIO_PORT }

# Stop previous listener on port if any
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$pidFile = Join-Path $script:Agent1Home "studio.pid"

$argList = @(
    "dev",
    "--config", $config,
    "--host", "127.0.0.1",
    "--port", "$port",
    "--no-browser"
)

Write-Host "Starting langgraph dev on 127.0.0.1:$port ..."
# Do NOT RedirectStandardOutput/Error — uvicorn logging fails (formatter 'simple')
# under Start-Process file redirects on Windows.
$proc = Start-Process -FilePath $cli -ArgumentList $argList -WorkingDirectory $appDir `
    -WindowStyle Minimized -PassThru
Set-Content -Path $pidFile -Value $proc.Id -Encoding ascii

$deadline = (Get-Date).AddSeconds(90)
$ok = $false
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) {
        Write-Error "langgraph dev exited early (code $($proc.ExitCode)). Check console / Event Viewer."
    }
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/ok" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {
        try {
            $r2 = Invoke-WebRequest -Uri "http://127.0.0.1:$port/docs" -UseBasicParsing -TimeoutSec 2
            if ($r2.StatusCode -eq 200) { $ok = $true; break }
        } catch { }
    }
    Start-Sleep -Seconds 2
}

if (-not $ok) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Write-Error "Agent Server did not become ready on :$port within timeout."
}

Write-Host "Studio Agent Server started (PID $($proc.Id))"
Write-Host "API:  http://127.0.0.1:$port"
Write-Host "Docs: http://127.0.0.1:$port/docs"
Write-Host "UI:   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:$port"

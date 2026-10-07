# Add the "Gateway / IAM / Cabinet / BL" block from .env.example to .env (missing keys only)
# and fill empty / "change-me" secrets with random values. Idempotent; never prints secrets.
# powershell -ExecutionPolicy Bypass -File infra\authentik\init-env.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$repo = Get-RepoRoot
$envFile = Join-Path $repo ".env"
$example = Join-Path $repo ".env.example"
if (-not (Test-Path $envFile)) { Copy-Item $example $envFile; Write-Host "Created .env from .env.example" }

# 1) missing keys from the example block
$inBlock = $false
$existing = @{}
foreach ($line in Get-Content $envFile) {
    if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=") { $existing[$Matches[1]] = $true }
}
$added = @()
foreach ($line in Get-Content $example) {
    if ($line -match "^# --- Gateway / IAM / Cabinet / BL") { $inBlock = $true; continue }
    if (-not $inBlock) { continue }
    if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$" -and -not $existing.ContainsKey($Matches[1])) {
        Add-Content -Path $envFile -Value $line -Encoding utf8
        $added += $Matches[1]
    }
}
if ($added.Count) { Write-Host ("Added keys: " + ($added -join ", ")) }

# 2) secrets
$secrets = [ordered]@{
    AUTHENTIK_SECRET_KEY         = 64
    AUTHENTIK_DB_PASSWORD        = 32
    AUTHENTIK_BOOTSTRAP_PASSWORD = 20
    AUTHENTIK_BL_TOKEN           = 48
    OIDC_CLIENT_SECRET           = 64
    AUTH_SECRET                  = 48
}
foreach ($k in $secrets.Keys) {
    $cur = Read-DotEnvValue -Path $envFile -Key $k -Default ""
    if (-not $cur -or $cur -eq "change-me") {
        Set-DotEnvValue -Path $envFile -Key $k -Value (New-RandomSecret -Length $secrets[$k])
        Write-Host "Generated $k"
    }
}
Write-Host ""
Write-Host "Done. Authentik admin login: user 'akadmin', password = AUTHENTIK_BOOTSTRAP_PASSWORD in .env"

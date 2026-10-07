# Optional fallback: map *.localhost names to 127.0.0.1 in the hosts file (needs Administrator).
# Usually not needed: Windows/.NET/Node/Chromium resolve *.localhost to loopback already.
# powershell -ExecutionPolicy Bypass -File infra\nginx\local\add-hosts.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$envFile = Join-Path (Get-RepoRoot) ".env"
$names = @(
    ([Uri](Read-DotEnvValue -Path $envFile -Key "PUBLIC_SITE_URL" -Default "http://alexsoft.localhost:8000")).Host,
    ([Uri](Read-DotEnvValue -Path $envFile -Key "AUTH_PUBLIC_URL" -Default "http://auth.alexsoft.localhost:8000")).Host
)

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Re-launching as Administrator (confirm UAC) ..."
    $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -Wait -PassThru -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    exit $p.ExitCode
}

$hosts = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"
$content = Get-Content -Raw $hosts
foreach ($n in $names) {
    if ($content -notmatch "(?m)^\s*127\.0\.0\.1\s+$([regex]::Escape($n))\b") {
        Add-Content -Path $hosts -Value "127.0.0.1 $n # alexsoft" -Encoding ascii
        Write-Host "added $n"
    } else { Write-Host "present $n" }
}

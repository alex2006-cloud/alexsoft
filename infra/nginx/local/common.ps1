# Shared helpers for the local Nginx gateway (native Windows, ADR-0020). Dot-source from sibling scripts.

$script:NginxVersion = if ($env:NGINX_VERSION) { $env:NGINX_VERSION } else { "1.30.5" }
$script:NginxHome = Join-Path $env:LOCALAPPDATA "AlexsoftNginx"
$script:NginxDir = Join-Path $script:NginxHome ("nginx-" + $script:NginxVersion)
$script:NginxExe = Join-Path $script:NginxDir "nginx.exe"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

function Read-DotEnvValue {
    param([string]$Path, [string]$Key, [string]$Default = "")
    if (-not (Test-Path $Path)) { return $Default }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Key\s*=\s*(.*)$") {
            $v = $Matches[1].Trim().Trim('"').Trim("'")
            if ($v) { return $v }
            return $Default
        }
    }
    return $Default
}

function ConvertTo-NginxPath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Expand-Template {
    param([string]$Text, [hashtable]$Values)
    foreach ($k in $Values.Keys) { $Text = $Text.Replace("@@$k@@", [string]$Values[$k]) }
    if ($Text -match "@@[A-Z_]+@@") { Write-Error "Unresolved placeholder: $($Matches[0])" }
    return $Text
}

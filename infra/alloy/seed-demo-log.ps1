# Append demo log lines for Alloy → Loki pipeline (Windows file-share safe).
# powershell -ExecutionPolicy Bypass -File infra\alloy\seed-demo-log.ps1

$ErrorActionPreference = "Stop"

$demoDir = Join-Path $env:LOCALAPPDATA "Alloy\demo"
$demoLog = Join-Path $demoDir "app.log"
New-Item -ItemType Directory -Force -Path $demoDir | Out-Null

if (-not (Test-Path $demoLog)) {
    # Create empty file without exclusive lock leftovers
    [System.IO.File]::WriteAllText($demoLog, "")
}

$ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$lines = @(
    "$ts level=info service=alloy-demo msg=`"alexsoft demo log line`"",
    "$ts level=info service=alloy-demo msg=`"pipeline check ok`""
)

$share = [System.IO.FileShare]::ReadWrite
$fs = [System.IO.File]::Open(
    $demoLog,
    [System.IO.FileMode]::Append,
    [System.IO.FileAccess]::Write,
    $share
)
try {
    $sw = New-Object System.IO.StreamWriter($fs, [System.Text.UTF8Encoding]::new($false))
    try {
        foreach ($line in $lines) {
            $sw.WriteLine($line)
        }
    } finally {
        $sw.Dispose()
    }
} finally {
    $fs.Dispose()
}

Write-Host "Appended $($lines.Count) lines -> $demoLog"
# Read with share as well
$fsRead = [System.IO.File]::Open($demoLog, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
try {
    $sr = New-Object System.IO.StreamReader($fsRead)
    try {
        $all = $sr.ReadToEnd() -split "`r?`n" | Where-Object { $_ -ne "" }
        $all | Select-Object -Last 5 | ForEach-Object { Write-Host $_ }
    } finally {
        $sr.Dispose()
    }
} finally {
    $fsRead.Dispose()
}

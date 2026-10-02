<#
.SYNOPSIS
  Готовит файлы для витрины портфолио в artifacts/portfolio/.

.DESCRIPTION
  Запуск ручной, когда исходники изменились:
    powershell -ExecutionPolicy Bypass -File scripts/export-portfolio.ps1

  Что делает:
    1. Рядом с вашими файлами в artifacts/portfolio/ создаёт картинки:
         0001-use-case.puml -> 0001-use-case.svg
         0001-sequence.puml -> 0001-sequence.svg
         0001.bpmn          -> 0001.svg + 0001.png
       (любой *.puml и *.bpmn в корне портфолио)
    2. В artifacts/portfolio/architecture/ собирает материалы платформы:
       C4 (SVG из artifacts/generated), Component Diagram, OpenAPI (Redoc HTML),
       ADR-0007 и исходники для скачивания (.dsl, .puml, .yaml).

  Лендинг файлы не рендерит: он читает artifacts/portfolio/portfolio.yaml
  (apps/landing/scripts/collect-portfolio.mjs).

  Нужно: Java (PlantUML), Node + npx (BPMN, Redoc), Edge или Chrome (headless для BPMN).
  PlantUML рисует через Graphviz (dot), а если его нет, встроенным движком Smetana
  (Component Diagram в этом случае берётся из готового artifacts/generated).
  C4 берётся из artifacts/generated (workflow Structurizr или structurizr export).
#>
[CmdletBinding()]
param(
  [switch]$SkipPlantUml,
  [switch]$SkipBpmn,
  [switch]$SkipOpenApi
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$art = Join-Path $root "artifacts"
$out = Join-Path $art "portfolio"
$arch = Join-Path $out "architecture"
$tools = Join-Path $env:LOCALAPPDATA "alexsoft\portfolio-tools"

New-Item -ItemType Directory -Force -Path $arch, $tools | Out-Null

function Step($t) { Write-Host "==> $t" -ForegroundColor Cyan }

# --- Исходники платформы для скачивания ---
Step "Исходники для скачивания"
Copy-Item (Join-Path $art "adr\0007-edge-nginx-npm.md") (Join-Path $arch "adr-0007-edge-nginx.md") -Force
Copy-Item (Join-Path $art "architecture\uml-component-diagram.puml") (Join-Path $arch "component-diagram.puml") -Force
Copy-Item (Join-Path $art "architecture\c4-l1-l2-l3.dsl") (Join-Path $arch "c4.dsl") -Force
Copy-Item (Join-Path $art "api\rag.openapi.yaml") (Join-Path $arch "rag.openapi.yaml") -Force

# --- C4 (готовый экспорт Structurizr) ---
Step "C4 из artifacts/generated"
$c4 = [ordered]@{
  "SystemContext"           = "c4-l1-system-context"
  "Containers"              = "c4-l2-containers"
  "ComponentsEdge"          = "c4-l3-edge"
  "ComponentsBusinessLogic" = "c4-l3-business-logic"
  "ComponentsAgentPlatform" = "c4-l3-agent-platform"
  "ComponentsRAG"           = "c4-l3-rag"
  "ComponentsObservability" = "c4-l3-observability"
}
foreach ($k in $c4.Keys) {
  $svg = Join-Path $art "generated\$k.svg"
  if (-not (Test-Path $svg)) { throw "Нет $svg. Сначала экспортируйте C4 (structurizr export), см. artifacts/generated/README.md" }
  Copy-Item $svg (Join-Path $arch "$($c4[$k]).svg") -Force
}

# --- PlantUML ---
if (-not $SkipPlantUml) {
  Step "PlantUML"
  $jar = Join-Path $tools "plantuml.jar"
  if (-not (Test-Path $jar)) {
    Invoke-WebRequest "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" -OutFile $jar
  }
  $hasDot = [bool](Get-Command dot -ErrorAction SilentlyContinue)
  $layout = if ($hasDot) { @() } else { @("-Playout=smetana") }

  function Export-PlantUml($src, $destSvg) {
    $tmp = Join-Path $tools "puml-tmp"
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    & java -jar $jar -tsvg -charset UTF-8 @layout -o $tmp $src
    if ($LASTEXITCODE -ne 0) { throw "PlantUML завершился с ошибкой: $src" }
    $svg = Get-ChildItem $tmp -Filter *.svg | Select-Object -First 1
    if (-not $svg) { throw "PlantUML не создал SVG: $src" }
    Copy-Item $svg.FullName $destSvg -Force
    Write-Host "    $destSvg"
  }

  foreach ($puml in Get-ChildItem $out -Filter *.puml -File) {
    Export-PlantUml $puml.FullName ([IO.Path]::ChangeExtension($puml.FullName, ".svg"))
  }
  # Component diagram: с Graphviz рендерим сами, иначе берём готовый экспорт
  if ($hasDot) {
    Export-PlantUml (Join-Path $arch "component-diagram.puml") (Join-Path $arch "component-diagram.svg")
  } else {
    Copy-Item (Join-Path $art "generated\uml-component-diagram.svg") (Join-Path $arch "component-diagram.svg") -Force
  }
}

# --- BPMN (bpmn-to-image + headless Edge/Chrome) ---
if (-not $SkipBpmn) {
  Step "BPMN"
  $browser = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($browser) { $env:PUPPETEER_EXECUTABLE_PATH = $browser }
  $env:PUPPETEER_SKIP_DOWNLOAD = "true"
  Push-Location $tools
  try {
    foreach ($bpmn in Get-ChildItem $out -Filter *.bpmn -File) {
      $base = [IO.Path]::ChangeExtension($bpmn.FullName, $null).TrimEnd(".")
      & npx.cmd --yes bpmn-to-image --no-title --no-footer --scale=2 "$($bpmn.FullName);$base.png,$base.svg"
      if ($LASTEXITCODE -ne 0) { throw "bpmn-to-image завершился с ошибкой: $($bpmn.Name)" }
    }
  } finally { Pop-Location }
}

# --- OpenAPI -> Redoc ---
if (-not $SkipOpenApi) {
  Step "OpenAPI (Redoc)"
  Push-Location $tools
  try {
    & npx.cmd --yes "@redocly/cli" build-docs (Join-Path $arch "rag.openapi.yaml") -o (Join-Path $arch "rag-api.html")
    if ($LASTEXITCODE -ne 0) { throw "redocly build-docs завершился с ошибкой" }
  } finally { Pop-Location }
}

Step "Готово: $out"

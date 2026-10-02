# Портфолио (витрина лендинга)

Всё, что лежит здесь и описано в [`portfolio.yaml`](portfolio.yaml), попадает на блок «Портфолио» сайта. Лендинг при сборке сам берёт файлы из этой папки, копировать что-то в `apps/landing` руками не нужно ([ADR-0016](../adr/0016-portfolio-from-artifacts.md)).

Не путать с `artifacts/architecture/`: там architecture-as-code платформы. Сюда кладутся **готовые к показу** файлы (PDF, PNG, SVG, MD, YAML, HTML).

## Как добавить документ

1. Положить файл в эту папку (подпапки можно).
2. Дописать карточку в [`portfolio.yaml`](portfolio.yaml).
3. Закоммитить. CI соберёт лендинг (workflow Site срабатывает на `artifacts/portfolio/**`).

Локальная проверка: `cd apps/landing; npm run dev`. Перед запуском `predev` собирает витрину; после правки yaml dev-сервер перезапустить.

## Способы показа (`view`)

| view | Что видит посетитель |
|------|----------------------|
| `pdf` | PDF открывается в браузере |
| `html` | Готовая HTML-страница (например, Redoc для OpenAPI) |
| `text` | Читаемая страница на сайте из `.md` (относительные ссылки превращаются в текст) |
| `image` | Картинка с увеличением (SVG, PNG, JPG) |
| `gallery` | Несколько картинок с вкладками, список `images: [{label, file}]` |
| `download` | Только скачивание (Excel) |

`downloads` необязателен. Если не указан, скачивается основной файл. Пути задаются от этой папки.

## Что из чего получено

Файлы бизнес-кейса и целевая схема лежат в корне папки. Картинки диаграмм рядом с исходниками рендерит `scripts/export-portfolio.ps1`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/export-portfolio.ps1
```

| Результат | Источник |
|-----------|----------|
| `0001-use-case.svg`, `0001-sequence.svg` | `*.puml` в этой папке (PlantUML) |
| `0001.svg`, `0001.png` | `0001.bpmn` (bpmn-to-image, Edge headless) |
| `architecture/c4-*.svg` | `artifacts/generated/` (экспорт Structurizr) |
| `architecture/component-diagram.*`, `c4.dsl`, `rag.openapi.yaml`, `adr-0007-*.md` | копии из `artifacts/architecture`, `api`, `adr` |
| `architecture/rag-api.html` | `rag.openapi.yaml` через Redocly (страница тянет скрипт Redoc с CDN) |
| `architecture-in-drawio.jpg` | снимок схемы draw.io, кладётся вручную |

Скрипт ничего не удаляет и перезаписывает только эти производные файлы. После правки исходника платформы запустите его и закоммитите обновлённые файлы. Автоматической проверки свежести нет.

## Именование

Латиница, kebab-case, без пробелов (кроме уже существующих файлов). `id` карточки: kebab-case, уникальный, не `files`.

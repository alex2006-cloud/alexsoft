# Артефакты архитектуры

Источник правды — **architecture-as-code**.

| Путь | Содержимое |
|------|------------|
| `architecture/c4-l1-l2-l3.dsl` | C4-модель — **править здесь** |
| `workspace.dsl` | Полная копия `c4-l1-l2-l3.dsl` для Structurizr Local (volume = `artifacts/`) |
| `workspace.json` | Раскладка блоков в UI Local (генерируется, руками не править) |
| `architecture/workspace.dsl` | Тонкий файл `!include c4-l1-l2-l3.dsl` — только для CLI |
| `architecture/architecture-in-drawio.drawio` | Целевая схема draw.io ([ADR-0015](adr/0015-target-architecture-stacks.md)) |
| `architecture/uml-component-diagram.puml` | UML Component Diagram |
| `api/rag.openapi.yaml` | OpenAPI-контракт RAG-сервиса (`apps/rag`) |
| `business-cases/` | User Story, Use Case, BPMN, Sequence |
| `adr/` | Architecture Decision Records |
| `generated/` | PNG/SVG из CI |
| `portfolio/` | Витрина для блока «Портфолио» лендинга: готовые файлы + `portfolio.yaml` ([ADR-0016](adr/0016-portfolio-from-artifacts.md)) |

## Structurizr Local

Порт: **8070** (`STRUCTURIZR_PORT`). Не 8080 (LiteLLM).

Local открывает только `workspace.dsl` в корне своего volume и не умеет загружать файл, состоящий лишь из `!include`. Поэтому `artifacts/workspace.dsl` — полная копия модели. После правок C4 синхронизируй:

```powershell
Copy-Item artifacts/architecture/c4-l1-l2-l3.dsl artifacts/workspace.dsl -Force
```

Запуск:

```bash
docker rm -f alexsoft-structurizr 2>/dev/null
docker run -d --name alexsoft-structurizr -p 8070:8080 \
  -v "${PWD}/artifacts:/usr/local/structurizr" \
  structurizr/structurizr local
```

http://localhost:8070

CLI / CI:

```bash
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright validate -workspace artifacts/architecture/c4-l1-l2-l3.dsl
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright export -workspace artifacts/architecture/c4-l1-l2-l3.dsl -format png -output artifacts/generated
```

## OpenAPI (Swagger UI)

```bash
docker run -d --name alexsoft-swagger -p 8071:8080 \
  -e SWAGGER_JSON=/spec/rag.openapi.yaml \
  -v "${PWD}/artifacts/api:/spec:ro" swaggerapi/swagger-ui
```

http://localhost:8071. Проверка контракта: `docker run --rm -v "${PWD}/artifacts/api:/spec" redocly/cli lint /spec/rag.openapi.yaml`.

# Артефакты архитектуры

Источник правды — **architecture-as-code**.

| Папка | Содержимое |
|-------|------------|
| `architecture/` | C4 L1–L3 (`c4-l1-l2-l3.dsl` + `workspace.dsl`), draw.io, `uml-component-diagram.puml` |
| `business-cases/` | User Story, Use Case, BPMN, Sequence по кейсам |
| `adr/` | Architecture Decision Records |
| `generated/` | PNG/SVG, которые собирает CI из DSL |

## Structurizr локально

Порт на хосте: **8070** (`STRUCTURIZR_PORT` в `.env`). **8080** занят LiteLLM — не публиковать Structurizr на host `:8080`.

**Править:** `artifacts/architecture/c4-l1-l2-l3.dsl`.  
`workspace.dsl` в той же папке не трогать — Structurizr Local открывает только это имя; внутри `!include` на C4-модель.

Вариант A — [Structurizr Local](https://docs.structurizr.com/local) (Docker):

```bash
docker run -d --name alexsoft-structurizr -p 8070:8080 \
  -v "${PWD}/artifacts/architecture:/usr/local/structurizr" \
  structurizr/structurizr local
```

Открыть http://localhost:8070.

Вариант B — GitHub Actions / CLI:

```bash
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright validate -workspace artifacts/architecture/c4-l1-l2-l3.dsl
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright export -workspace artifacts/architecture/c4-l1-l2-l3.dsl -format png -output artifacts/generated
```

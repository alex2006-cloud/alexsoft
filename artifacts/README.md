# Артефакты архитектуры

Источник правды — **architecture-as-code**.

| Папка | Содержимое |
|-------|------------|
| `structurizr/` | Workspace DSL: C4, use cases, компоненты |
| `adr/` | Architecture Decision Records |
| `generated/` | PNG/SVG, которые собирает CI из DSL |

## Structurizr локально

Вариант A — [Structurizr Lite](https://docs.structurizr.com/lite) (Docker):

```bash
docker run -it --rm -p 8080:8080 -v "${PWD}/artifacts/structurizr:/usr/local/structurizr" structurizr/lite
```

Открыть http://localhost:8080 — workspace подхватит `workspace.dsl`.

Вариант B — GitHub Actions: workflow `.github/workflows/structurizr.yml` проверяет DSL и выгружает PNG/SVG в `generated/` при push. Локально то же через Docker:

```bash
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright validate -workspace artifacts/structurizr/workspace.dsl
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright export -workspace artifacts/structurizr/workspace.dsl -format png -output artifacts/generated
```

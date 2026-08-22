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

Вариант B — [Structurizr CLI](https://docs.structurizr.com/cli) для экспорта в CI (этап GitHub Actions).

Сюда GitHub Actions кладёт экспорт диаграмм из `artifacts/structurizr/workspace.dsl` (PNG и SVG).

Источник правды — DSL, не картинки. После изменения `workspace.dsl` и push в `main` workflow **Structurizr** пересобирает файлы и коммитит их сюда.

Прогон можно запустить вручную: репозиторий → Actions → Structurizr → Run workflow.

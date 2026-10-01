Сюда GitHub Actions кладёт экспорт диаграмм из `artifacts/architecture/c4-l1-l2-l3.dsl` (PNG и SVG).

Источник правды — DSL (`c4-l1-l2-l3.dsl`), не картинки. После изменения DSL и push в `main` workflow **Structurizr** пересобирает файлы и коммитит их сюда.

Прогон можно запустить вручную: репозиторий → Actions → Structurizr → Run workflow.

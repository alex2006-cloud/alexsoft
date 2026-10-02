Сюда кладётся экспорт диаграмм из `artifacts/architecture/c4-l1-l2-l3.dsl` (PNG и SVG) и UML Component Diagram.

Источник правды — DSL / `.puml` / draw.io, не картинки.

**C4 (Structurizr):** после изменения `c4-l1-l2-l3.dsl` и push в `main` workflow **Structurizr** пересобирает файлы. Локально:

```bash
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright export -workspace artifacts/architecture/c4-l1-l2-l3.dsl -format png -output artifacts/generated
docker run --rm -v "${PWD}:/usr/local/structurizr" structurizr/structurizr:2026.06.28-playwright export -workspace artifacts/architecture/c4-l1-l2-l3.dsl -format svg -output artifacts/generated
```

**UML:** из `uml-component-diagram.puml` → `uml-component-diagram.png` / `.svg` в этой папке (PlantUML Docker).

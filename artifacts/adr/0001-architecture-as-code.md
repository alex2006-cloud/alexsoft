# ADR-0001: Architecture-as-code через Structurizr

- **Статус:** accepted
- **Дата:** 2026-08-22
- **Контекст:** Нужны живые артефакты C4 / use cases / компоненты и ADR, которые не расходятся с репозиторием. Ручные картинки в Confluence/Draw.io быстро устаревают.
- **Решение:** Источник правды — `artifacts/structurizr/workspace.dsl`. Диаграммы экспортируются CLI в CI при push. Решения по архитектуре фиксируются в `artifacts/adr/`. C4 ведётся по уровням: сейчас L1 (System Context), L2/L3 и use cases дополняются по мере появления сервисов.
- **Последствия:** Любое изменение границ системы начинается с DSL и при необходимости ADR. Рендер в Structurizr Lite локально; публикация картинок — из `artifacts/generated` после появления GitHub Actions.

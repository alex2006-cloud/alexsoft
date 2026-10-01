# ADR-0001: Architecture-as-code через Structurizr

- **Статус:** accepted
- **Дата:** 2026-08-22
- **Контекст:** Нужны живые артефакты C4 / use cases / компоненты и ADR, которые не расходятся с репозиторием. Ручные картинки в Confluence/Draw.io быстро устаревают.
- **Решение:** Источник правды — `artifacts/architecture/c4-l1-l2-l3.dsl` (нотация C4 уровней 1–2–3). Файл `artifacts/architecture/workspace.dsl` содержит только `!include` — Structurizr Local по умолчанию открывает именно это имя; править модель в `c4-l1-l2-l3.dsl`. Диаграммы экспортируются CLI в CI при push. Решения по архитектуре фиксируются в `artifacts/adr/`. C4 ведётся по уровням: L1 (System Context), L2 (Containers), L3 (Components) — дополняются по мере появления сервисов.
- **Последствия:** Любое изменение границ системы начинается с DSL и при необходимости ADR. Рендер в Structurizr Lite локально; публикация картинок — из `artifacts/generated` после появления GitHub Actions.

# ADR-0001: Architecture-as-code через Structurizr

- **Статус:** accepted
- **Дата:** 2026-08-22
- **Контекст:** Нужны живые артефакты C4 / use cases / компоненты и ADR, которые не расходятся с репозиторием. Ручные картинки в Confluence/Draw.io быстро устаревают.
- **Решение:** Источник правды — `artifacts/architecture/c4-l1-l2-l3.dsl` (нотация C4 уровней 1–2–3). Structurizr Local жёстко ищет `workspace.dsl` в data directory; чтобы не плодить вторую копию модели, `workspace.dsl` — NTFS hardlink на `c4-l1-l2-l3.dsl` (один inode). Docker volume = `artifacts/architecture/`. Диаграммы экспортируются CLI в CI при push. Решения по архитектуре фиксируются в `artifacts/adr/`. C4: L1 / L2 / L3.
- **Последствия:** Любое изменение границ системы начинается с DSL и при необходимости ADR. Рендер в Structurizr Lite локально; публикация картинок — из `artifacts/generated` после появления GitHub Actions.

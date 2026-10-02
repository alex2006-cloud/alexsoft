# ADR-0016: Портфолио лендинга публикуется из artifacts/portfolio

- **Статус:** accepted
- **Дата:** 2026-10-02
- **Контекст:** В блоке «Портфолио» лендинга нужны методики, документы бизнес-кейса и архитектурные схемы (C4, UML, BPMN, OpenAPI, ADR). Раньше файлы копировались руками в `apps/landing/public/portfolio` и описывались в `site.ts`: две копии, правка кода при каждом документе. Лендинг остаётся витриной без бизнес-логики и не должен знать о конкретных документах.
- **Рассмотренные альтернативы:**
  - Рендерить диаграммы при сборке лендинга в CI (Docker, headless-браузер): дольше сборка, тяжёлый CI, локально без Docker не посмотреть.
  - Указатели на исходники в `artifacts/architecture` и сборка картинок на лету: нет контроля над тем, что показывать.
- **Решение:**
  - Единственное место публикации: `artifacts/portfolio/` (готовые к показу файлы) и индекс `portfolio.yaml` (группы, карточки, способ показа).
  - При `predev` и `prebuild` скрипт `apps/landing/scripts/collect-portfolio.mjs` проверяет индекс, копирует файлы в `public/portfolio/files/` и пишет `src/content/portfolio.generated.json`. Оба пути в `.gitignore`, это вывод скрипта.
  - Картинки диаграмм готовит `scripts/export-portfolio.ps1` (PlantUML, bpmn-to-image, Redocly) и коммитятся в `artifacts/portfolio/`. Рендера в CI нет.
  - Workflow Site срабатывает на `artifacts/portfolio/**`.
- **Последствия:**
  - Новый документ = файл в `artifacts/portfolio/` + запись в `portfolio.yaml`; код лендинга не меняется.
  - Ошибки индекса (нет файла, дубль `id`, неизвестная группа) роняют сборку с понятным сообщением.
  - Готовые файлы дублируют исходники платформы; свежесть обеспечивается ручным запуском `export-portfolio.ps1`.
  - Redoc-страница OpenAPI подгружает скрипт Redoc с CDN `cdn.redocly.com`.
- **Ссылки:** [`artifacts/portfolio/README.md`](../portfolio/README.md), [`apps/landing/scripts/collect-portfolio.mjs`](../../apps/landing/scripts/collect-portfolio.mjs)

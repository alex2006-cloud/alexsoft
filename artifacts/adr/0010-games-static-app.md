# ADR-0010: Игры — отдельное Next.js-приложение, статика под `/games`

- **Статус:** accepted
- **Дата:** 2026-09-15
- **Контекст:** Этап 4 ROADMAP — первый продукт лаборатории без Docker. Нужен каталог игр с лендинга (блок Lab → «Игры»), несколько мини-игр в браузере, один деплой на VPS вместе с витриной (`output: "export"`, Nginx). Логику игр не смешивать с лендингом-визиткой ([AGENTS.md](../../AGENTS.md)).
- **Решение:**
  - **Вариант B:** отдельное приложение `apps/games` (Next.js, `output: "export"`, `basePath: "/games"`), порт dev **3010**.
  - **Лендинг** (`apps/landing`) — витрина: карточка Lab «Игры» → `/games` (статус Live). В dev — `rewrites` `/games` → `http://127.0.0.1:3010`.
  - **Игры (v1):** каталог `/games`; «Контур» (`/games/contour`), «Вайб-чек» (`/games/vibe-check`), «Десант» (`/games/desant`) — клиентская статика, без бэкенда и без Docker.
  - **CI (workflow Site / `landing.yml`):** `npm run build` landing + games → копирование `apps/games/out/` → `apps/landing/out/games/` → один `rsync` на VPS `/var/www/osipcraft`. URL вида `https://osipcraft.ru/games/...`.
  - **Не выбран вариант A** (игры внутри `apps/landing`): раздувает витрину и смешивает ответственность. **Не выбран Docker/Compose** на этом этапе: не нужен для статических мини-игр; Compose — позже на VPS по общей политике.
- **Последствия:**
  - Инструкция: [apps/games/README.md](../../apps/games/README.md).
  - Новый продукт-игра = страница в `apps/games` + запись в каталоге; лендинг только ссылка из Lab.
  - Structurizr: контейнер Games = Next.js (apps/games), связь landing → games по HTTPS-пути `/games`.
  - Этап 4 ROADMAP закрыт; следующий — этап 5 (AI-контур).

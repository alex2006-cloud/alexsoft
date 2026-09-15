# Games — Personal Ecosystem Lab

См. [ADR-0010](../../artifacts/adr/0010-games-static-app.md). Отдельное Next.js-приложение (`output: "export"`, `basePath: "/games"`).

На проде сборка **склеивается** с лендингом в CI и уезжает одним `rsync` в `/var/www/osipcraft` → URL вида `https://osipcraft.ru/games/...`.

## Локально

```powershell
cd C:\alexsoft\apps\games
npm install
npm run dev
```

Открыть: http://localhost:3010/games  

Порт **3010** (не 3002 — там Metabase).

Вместе с лендингом: `npm run dev` в `apps/landing` (:3000) **и** в `apps/games` (:3010).  
Лендинг в dev проксирует `/games` → `:3010` (см. `apps/landing/next.config.ts`).

## Игры

| Игра | URL (prod / через лендинг) |
|------|----------------------------|
| Каталог | `/games` |
| Вайб-чек | `/games/vibe-check` |
| Контур | `/games/contour` |
| Десант | `/games/desant` |

## Сборка

```powershell
cd C:\alexsoft\apps\games
npm run build
```

Статика в `apps/games/out/`. Для локальной проверки полного сайта:

```powershell
cd C:\alexsoft\apps\landing
npm run build
# затем скопировать games/out → landing/out/games
```

Или полагаться на GitHub Actions (workflow **Site** / `landing.yml`).

Этап 4 ROADMAP закрыт (2026-09-15).

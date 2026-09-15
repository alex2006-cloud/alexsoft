# Landing (Next.js)

Публичная визитка Алексея Осипова: личный лендинг в духе продуктовых страниц Apple, избранные работы и витрина лаборатории alexsoft.

Продуктовая логика игр, RAG и AI-шлюза сюда не кладётся — только ссылки и статус. Игры живут в [`apps/games`](../games).

## Запуск

```powershell
cd apps/landing
npm install
npm run dev
```

Открыть http://localhost:3000.

Для раздела «Игры» локально параллельно поднимите games (`npm run dev` в `apps/games` → `:3010`). В dev лендинг проксирует `/games` на games-приложение.

## Сборка

```powershell
npm run build
```

Для продакшена задайте `LANDING_URL=https://osipcraft.ru` перед `npm run build` (Open Graph и canonical).

## Деплой на VPS (osipcraft.ru)

При push в `main` с изменениями в `apps/landing/` **или** `apps/games/` workflow (**Site**, файл `landing.yml`) собирает:

1. статику лендинга;
2. статику игр (`basePath: /games`);
3. склеивает `games/out` → `landing/out/games`;
4. одним `rsync` выкладывает на VPS (`/var/www/osipcraft`).

Один раз добавьте секрет в GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значение |
|--------|----------|
| `LANDING_SSH_KEY` | приватный ключ SSH для `root@130.17.1.193` (весь файл `alexsoft_fornex`, включая `BEGIN`/`END`) |

В PowerShell скопируйте ключ **без искажений**:

```powershell
Get-Content $env:USERPROFILE\.ssh\alexsoft_fornex -Raw | Set-Clipboard
```

Вставьте в секрет и сохраните. Ключ **без парольной фразы**. Если deploy падает с `error in libcrypto` — секрет перезапишите этой командой.

Публичный ключ с этой пары должен быть в `/root/.ssh/authorized_keys` на сервере.

Проверка после push: https://osipcraft.ru и https://osipcraft.ru/games — или в Actions откройте job **deploy**.

PR только собирают сайт, на сервер не выкладывают.

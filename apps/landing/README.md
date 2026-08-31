# Landing (Next.js)

Публичная визитка Алексея Осипова: личный лендинг в духе продуктовых страниц Apple, избранные работы и витрина лаборатории alexsoft.

Продуктовая логика игр, RAG и AI-шлюза сюда не кладётся — только маршруты и статус «скоро».

## Запуск

```bash
cd apps/landing
npm install
npm run dev
```

Открыть [http://localhost:3000](http://localhost:3000).

## Сборка

```bash
npm run build
npm start
```

Для продакшена задай `LANDING_URL=https://osipcraft.ru` перед `npm run build` (Open Graph и canonical).

## Деплой на VPS (osipcraft.ru)

При push в `main` с изменениями в `apps/landing/` workflow **Landing** собирает статику и выкладывает её на VPS (`/var/www/osipcraft`).

Один раз добавь секрет в GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значение |
|--------|----------|
| `LANDING_SSH_KEY` | приватный ключ SSH для `root@130.17.1.193` (весь файл `alexsoft_fornex`, включая `BEGIN`/`END`) |

В PowerShell скопируй ключ **без искажений**:

```powershell
Get-Content $env:USERPROFILE\.ssh\alexsoft_fornex -Raw | Set-Clipboard
```

Вставь в секрет и сохрани. Ключ **без парольной фразы**. Если deploy падает с `error in libcrypto` — секрет перезапиши этой командой.

Публичный ключ с этой пары должен быть в `/root/.ssh/authorized_keys` на сервере.

Проверка после push: https://osipcraft.ru — или в Actions открой job **deploy**.

PR только собирают лендинг, на сервер не выкладывают.

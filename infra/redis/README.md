# Redis (локально, Windows)

См. [ADR-0005](../../artifacts/adr/0005-redis-native-local.md). Без Docker — **Memurai** (нативный Redis-совместимый сервер) + GUI **Redis Insight**.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| Memurai | `%LOCALAPPDATA%\Memurai` (ручная раскладка MSI: обычный `winget`/`msiexec` падает с 1603 на custom action) |
| Конфиг | `%LOCALAPPDATA%\Memurai\memurai.conf` |
| Данные/логи | `%LOCALAPPDATA%\Memurai\data\` |
| Redis Insight | `%LOCALAPPDATA%\Programs\Redis Insight\` |

Слушает `127.0.0.1:6379`. Пароль по умолчанию как в `.env.example`: **`change-me`** (сверь с `REDIS_PASSWORD` в своём `.env`).

## 1. Установка Memurai (если с нуля)

### Предпочтительный путь (если MSI ставится)

```powershell
winget install --id Memurai.MemuraiDeveloper -e --accept-package-agreements --accept-source-agreements
```

### Обходной путь (MSI 1603 / нет прав в Program Files)

Уже применено на этой машине:

1. Извлечь MSI: `msiexec /a Memurai-Developer-v4.1.2.msi /qn TARGETDIR=%TEMP%\MemuraiExtract`
2. Скопировать файлы в `%LOCALAPPDATA%\Memurai`
3. Взять `Samples\memurai.conf` → `memurai.conf`, включить `requirepass`, `bind 127.0.0.1`, `dir`/`logfile` → `data\`
4. Запуск: `start-memurai.ps1` в той же папке

## 2. Запуск / остановка

Из‑за Execution Policy на Windows запускай так:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Memurai\start-memurai.ps1"
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\Memurai\stop-memurai.ps1"
```

`start-memurai.ps1` берёт пароль из `requirepass` в `memurai.conf` (не из `.env`). После смены пароля правь **оба**: `.env` → `REDIS_PASSWORD` и `memurai.conf` → `requirepass`, затем рестарт.

Проверка (подставь свой пароль):

```powershell
& "$env:LOCALAPPDATA\Memurai\memurai-cli.exe" -h 127.0.0.1 -p 6379 -a ВАШ_ПАРОЛЬ --no-auth-warning PING
```

Ожидается `PONG`.

## 3. `.env`

```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=change-me
```

Пароль в `.env` и `requirepass` в `memurai.conf` должны совпадать.

## 4. Redis Insight (GUI)

Уже можно поставить так:

```powershell
winget install --id RedisInsight.RedisInsight -e --accept-package-agreements --accept-source-agreements
```

### Подключение

1. Открыть **Redis Insight** → **Add Redis database**.
2. Параметры:

| Поле | Значение |
|------|----------|
| Host | `127.0.0.1` |
| Port | `6379` |
| Database Alias | `alexsoft (local)` |
| Username | *(пусто)* |
| Password | тот же, что `REDIS_PASSWORD` / `requirepass` |

3. **Test Connection** → **Add Redis Database**.

CLI в Insight:

```
SET alexsoft:ping "ok"
GET alexsoft:ping
KEYS alexsoft:*
```

## Если Connection refused

- Memurai не запущен → `start-memurai.ps1`
- Неверный пароль → сверь `.env` и `requirepass` в `memurai.conf`
- Порт занят → `Get-NetTCPConnection -LocalPort 6379`

## Примечание про Windows Service

Обычный MSI с `INSTALL_SERVICE=1` на этой машине падает (`SFXCA: Failed to create temp directory`, код 5). Поэтому сейчас Memurai — пользовательский процесс, не служба. Автостарт со входом в Windows: ярлык в оболочку Startup или Task Scheduler на `start-memurai.ps1`. Полноценная служба — когда починится MSI/UAC или появится Docker.

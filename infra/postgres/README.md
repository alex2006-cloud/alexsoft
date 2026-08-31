# PostgreSQL (локально, Windows)

См. [ADR-0004](../../artifacts/adr/0004-postgresql-native-local.md). Без Docker — нативная установка PostgreSQL 16.

## 1. Установить PostgreSQL 16

1. Скачать установщик: [PostgreSQL for Windows](https://www.postgresql.org/download/windows/) (EDB installer).
2. В мастере установки:
   - версия **16**;
   - компоненты: **PostgreSQL Server**, **Command Line Tools**, при желании **pgAdmin**;
   - порт **5432**;
   - задать пароль суперпользователя **`postgres`** — запомнить (для первичной настройки).
3. Завершить установку. Служба **postgresql-x64-16** должна быть в статусе «Работает» (Win+R → `services.msc`).

Проверка в PowerShell (путь может отличаться):

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "SELECT version();"
```

## 2. Подготовить `.env`

Из корня репозитория:

```powershell
copy .env.example .env
```

В `.env` задайте один и тот же пароль в трёх местах:

```
POSTGRES_PASSWORD=ваш-пароль
DATABASE_URL=postgresql://alexsoft:ваш-пароль@localhost:5432/alexsoft
```

## 3. Создать роль и базу `alexsoft`

### Через DBeaver

1. **New Connection** → PostgreSQL → подключиться как **`postgres`** (пароль из установки), база **`postgres`**.
2. SQL-редактор → открыть `infra/postgres/setup/00-create-role-and-db.sql`, заменить `'change-me'` на пароль из `.env`.
3. **Выполнить только блок Part 1** (DO $$ … $$) — выделить его → Ctrl+Enter.
4. SQL-редактор → открыть `infra/postgres/setup/01-create-database.sql` → выполнить **отдельно** (Ctrl+Enter).

   > DBeaver выполняет несколько команд в одной транзакции; `CREATE DATABASE` в транзакции запрещён — отсюда ошибка «нельзя выполнять в конвейере».

5. Подключение **alexsoft**: New Connection → user **`alexsoft`**, database **`alexsoft`**, тот же пароль.
6. На подключении **alexsoft** выполнить `infra/postgres/init/01-extensions.sql`.

### Через psql

```powershell
cd C:\alexsoft
# отредактировать пароль в setup/00-create-role-and-db.sql, затем:
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -f infra/postgres/setup/00-create-role-and-db.sql
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U alexsoft -d alexsoft -f infra/postgres/init/01-extensions.sql
```

## 4. Проверка

В DBeaver на базе **alexsoft**:

```sql
SELECT current_database(), current_user, version();
```

Расширения: `\dx` в psql или в DBeaver → **Extensions** — `uuid-ossp`, `pgcrypto`.

## Параметры подключения (DBeaver)

| Поле | Значение |
|------|----------|
| Host | `localhost` |
| Port | `5432` |
| Database | `alexsoft` |
| Username | `alexsoft` |
| Password | из `.env` → `POSTGRES_PASSWORD` |

## Подключение через Cursor / VS Code

Расширения **SQLTools** + **SQLTools PostgreSQL/Cockroach Driver** (рекомендованы в `.vscode/extensions.json`).

1. Cursor предложит установить рекомендуемые расширения — **Install**, либо вручную: `Ctrl+Shift+X` → найти **SQLTools** и **SQLTools Driver PostgreSQL**.
2. После установки слева появится иконка **SQLTools** (цилиндр).
3. В панели SQLTools: **alexsoft (local)** → подключиться; пароль — из `.env` (`POSTGRES_PASSWORD`).
4. **New SQL File** → писать запросы → выделить → **Run on active connection** (`Ctrl+E Ctrl+E`).

Пароль в репозиторий не кладётся (`askForPassword: true` в `.vscode/settings.json`).

## Если «Connection refused»

- Служба PostgreSQL не запущена → `services.msc` → **postgresql-x64-16** → Запустить.
- Неверный порт → в установщике мог быть другой порт; проверить в pgAdmin или `services.msc`.

## Альтернатива: Docker

`infra/compose/docker-compose.data.yml` — по [ADR-0003](../compose/docker-compose.data.yml) (superseded для Windows-разработки). Использовать только если установлен Docker Desktop.

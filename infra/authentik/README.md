# Authentik (IdP, Docker Compose + БД в нативном Postgres)

Единый вход (OIDC) для кабинета и API: [ADR-0019](../../artifacts/adr/0019-cabinet-ssr-bff-authentik.md), топология — [ADR-0020](../../artifacts/adr/0020-local-iam-gateway-topology.md).

**Исключение из «нативно на ноутбуке»:** у Authentik нет сборки под Windows (официально — только образы), поэтому `server` + `worker` идут в Docker Compose (как Dify). База данных **не в контейнере**: это БД `authentik` в уже установленном PostgreSQL 16. Redis не нужен (убран с 2025.10).

## Предусловия

- Docker Desktop (скрипт запуска сам стартует его при необходимости)
- PostgreSQL 16 запущен (`postgresql-x64-16`)
- Порт **9100** свободен (9000 занят MinIO)

## Первая установка (один раз)

```powershell
# 1. секреты и переменные в .env (идемпотентно, значения не печатаются)
powershell -ExecutionPolicy Bypass -File infra\authentik\init-env.ps1
# 2. роль и БД authentik в нативном Postgres
powershell -ExecutionPolicy Bypass -File infra\authentik\setup-db.ps1
# 3. доступ контейнера к Postgres хоста (pg_hba + firewall; запросит UAC)
powershell -ExecutionPolicy Bypass -File infra\authentik\configure-postgres.ps1
# 4. старт (первый раз — миграции, несколько минут)
powershell -ExecutionPolicy Bypass -File infra\authentik\start-authentik.ps1
```

Остановка: `stop-authentik.ps1`. Опционально: `scripts\dev-up.ps1 -WithAuth`.

## Что создаёт blueprint

[`blueprints/alexsoft.yaml`](blueprints/alexsoft.yaml) монтируется в `/blueprints/custom` и применяется воркером автоматически:

| Объект | Назначение |
|--------|-----------|
| группы `alexsoft-users`, `alexsoft-admins` | роли `user` / `admin` (claim `groups`) |
| OIDC-провайдер и приложение `alexsoft-cabinet` | вход кабинета: Authorization Code, confidential-клиент, подпись RS256 (JWKS) |
| flow `alexsoft-enrollment` | саморегистрация: имя пользователя, имя, email, пароль; новый пользователь сразу в `alexsoft-users` |
| ссылка «Регистрация» | привязана к `default-authentication-identification` |
| сервисный пользователь `alexsoft-bl` + токен | BL читает пользователей / деактивирует их через API Authentik |

Назначить администратора кабинета: Authentik Admin → Directory → Groups → `alexsoft-admins` → добавить пользователя.

## Адреса

| Что | Адрес |
|-----|-------|
| Authentik напрямую | http://127.0.0.1:9100 (admin: `/if/admin/`, пользователь `akadmin`, пароль `AUTHENTIK_BOOTSTRAP_PASSWORD` из `.env`) |
| Через gateway (для браузера и OIDC) | http://auth.alexsoft.localhost:8000 |
| OIDC discovery | `http://auth.alexsoft.localhost:8000/application/o/alexsoft-cabinet/.well-known/openid-configuration` |
| JWKS (для BL, напрямую) | `http://127.0.0.1:9100/application/o/alexsoft-cabinet/jwks/` |

## Если контейнер не видит Postgres

Симптом: `server` перезапускается, в логах `connection refused` / `no pg_hba.conf entry`. Проверьте, что выполнен шаг 3 и что сервис `postgresql-x64-16` запущен. Запасной план — Postgres внутри Compose (добавить сервис `postgresql` и поменять `AUTHENTIK_POSTGRESQL__HOST`), см. ADR-0020.

## Обновление версии

Тег образа — `AUTHENTIK_TAG` (по умолчанию в `compose.yml`). Перед обновлением прочитайте release notes и сделайте дамп БД `authentik`.

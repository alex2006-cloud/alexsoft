# BL API (`apps/api`)

FastAPI-сервис бизнес-логики для кабинета. Контракт (contract-first): [`artifacts/api/bl.openapi.yaml`](../../artifacts/api/bl.openapi.yaml). Решения: [ADR-0019](../../artifacts/adr/0019-cabinet-ssr-bff-authentik.md), [ADR-0020](../../artifacts/adr/0020-local-iam-gateway-topology.md).

- Слушает только `127.0.0.1:8100`, наружу не проксируется. Единственный клиент — BFF кабинета (`apps/cabinet`).
- **JWT проверяется здесь** по JWKS Authentik (`iss`, `aud` = `OIDC_CLIENT_ID`, `exp`, RS256); роли из claim `groups`: `alexsoft-users` → `user`, `alexsoft-admins` → `user`+`admin`. Nginx JWT не проверяет.
- Данные: схема `bl` в БД `alexsoft` (создаётся при старте): `agents`, `runs`, `run_events`, `settings`.
- Квота: суточное число запусков на пользователя (`BL_DAILY_RUN_QUOTA`, по умолчанию 20; админ меняет в `/v1/admin/settings`), ответ `429` + `Retry-After`.
- Запуск агента: `POST /v1/agents/{id}/runs` → `202`, ход — SSE `GET /v1/runs/{id}/events` (`status`, `step`, `message`, `done`, `error`).

## Агенты и подключение БП1

Реестр агентов — таблица `bl.agents` (seed в [`alexsoft_api/agents/__init__.py`](alexsoft_api/agents/__init__.py), правки админа сохраняются):

| id | kind | состояние |
|----|------|-----------|
| `echo-demo` | `echo` | включён; заглушка без LLM |
| `agent1-qa` | `langgraph` | включён; граф `agent1_qa` на Agent Server `:2024` (нужны LiteLLM и Studio) |
| `bp1-project-qa` | `langgraph` | включён; агент БП1 «Q&A по проекту» — граф `bp1_qa` (нужны Studio `:2024`, RAG `:8200`, LiteLLM) |

Seed вставляется с `ON CONFLICT DO NOTHING`: в уже существующей БД состояние агента меняется в админ-панели кабинета (или `PATCH /v1/admin/agents/bp1-project-qa`), а не правкой seed. Агент БП1 описан в [`apps/agent1/README.md`](../agent1/README.md). Новый тип запуска (не LangGraph) — это новый класс `AgentRunner` в `alexsoft_api/agents/` и ключ в `build_runners`. `trace_id` запуска = `run_id` Agent Server (совпадает с трейсом LangSmith при включённом трейсинге).

Пока нет RabbitMQ (этап 6), BL вызывает Agent Platform напрямую по HTTP — временная связь, отражена в C4.

## Запуск

```powershell
powershell -ExecutionPolicy Bypass -File infra\api\install-api.ps1   # venv в %LOCALAPPDATA%\AlexsoftApi
powershell -ExecutionPolicy Bypass -File infra\api\test-api.ps1      # тесты (без Postgres и Authentik)
powershell -ExecutionPolicy Bypass -File infra\api\start-api.ps1     # http://127.0.0.1:8100/docs
powershell -ExecutionPolicy Bypass -File infra\api\stop-api.ps1
```

Переменные — корневой `.env` (`BL_*`, `OIDC_*`, `AUTH_PUBLIC_URL`, `AUTHENTIK_*`, `POSTGRES_*`), шаблон `.env.example`. `GET /health/ready` проверяет Postgres и JWKS Authentik.

# Dify (Docker Compose)

Этап **5.4** — low-code AI platform. LLM только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)).

**Исключение:** на ноутбуке Dify ставится через **Docker Compose** (официальный путь). AutoGen и n8n остаются нативными.

## Предусловия

- Docker Desktop установлен и **запущен**
- Порт **3003** свободен (не 3000 — лендинг; не 3001 Grafana; не 3002 Metabase)

## Где лежит на машине

| Компонент | Путь |
|-----------|------|
| Clone upstream | `%LOCALAPPDATA%\AlexsoftDify\repo\` (не в git monorepo) |
| Compose + `.env` | `%LOCALAPPDATA%\AlexsoftDify\repo\docker\` |

| Сервис | URL |
|--------|-----|
| Dify GUI | http://127.0.0.1:3003 |
| LiteLLM (хост) | http://127.0.0.1:8080 |
| LiteLLM (из контейнера) | http://host.docker.internal:8080/v1 |

## Установка

```powershell
powershell -ExecutionPolicy Bypass -File infra\dify\install-dify.ps1
```

Скрипт клонирует `langgenius/dify` (тег `DIFY_GIT_REF`, по умолчанию `1.11.1`) и выставляет `EXPOSE_NGINX_PORT=$DIFY_WEB_PORT`.

## Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\dify\start-dify.ps1
powershell -ExecutionPolicy Bypass -File infra\dify\stop-dify.ps1
```

Опционально: `scripts\dev-up.ps1 -WithDify` / `dev-down.ps1 -WithDify`.

Первый `up` может долго тянуть образы.

## LiteLLM в UI

1. Откройте http://127.0.0.1:3003 и завершите initial setup (admin).
2. **Settings → Model Provider** → **OpenAI-API-compatible** (или аналог).
3. **API Base / Base URL:** `http://host.docker.internal:8080/v1`  
   (`localhost` из контейнера — не хост Windows.)
4. **API Key:** `LITELLM_MASTER_KEY` из `.env` репозитория alexsoft.
5. Модель: алиас LiteLLM `deepseek` (или `qwen`).

Не подключайте провайдеров в обход LiteLLM.

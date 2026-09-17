# LiteLLM (локально, Windows)

См. [ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md). Нативный **AI Gateway** этапа 5.1: Python venv + `litellm[proxy]`. OpenAI-compatible API к облачным LLM. **Подключены:** **DeepSeek** (рабочий путь) и **Qwen** (DashScope, опционально). Не путать с API Gateway / IAM (этап 6). Docker/Compose — на этапе VPS.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| venv + `litellm` | `%LOCALAPPDATA%\LiteLLM\venv\` |
| Рабочий `config.yaml` | `%LOCALAPPDATA%\LiteLLM\config.yaml` (копия из репо при старте) |
| stdout/stderr | `%LOCALAPPDATA%\LiteLLM\litellm.out.log` / `litellm.err.log` |

API: `http://127.0.0.1:8080` (порт из `.env` → `LITELLM_PORT`).

| Алиас | Провайдер | Ключ в `.env` |
|-------|-----------|---------------|
| **`deepseek`** | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| **`qwen`** | `dashscope/qwen-plus` | `DASHSCOPE_API_KEY` |

## Зависимости

1. **Python 3.11+** (рекомендация: 3.12).
   ```powershell
   winget install --id Python.Python.3.12 -e
   python --version
   ```
   `install-litellm.ps1` попытается поставить Python через winget, если его ещё нет.
2. **PostgreSQL** (уже с этапа 2) — БД/схема **`litellm`** для Admin UI (Prisma). `setup-db.ps1` создаёт отдельную БД `litellm` или, если нет прав, схему `litellm` в БД `alexsoft`.
3. Ключ в локальном `.env`: минимум **`DEEPSEEK_API_KEY`** (platform.deepseek.com).  
   Опционально Qwen: `DASHSCOPE_API_KEY`; ключ DashScope региона China/Beijing → также `DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1`.

## 1. Установка

```powershell
powershell -ExecutionPolicy Bypass -File infra\litellm\install-litellm.ps1
powershell -ExecutionPolicy Bypass -File infra\litellm\setup-db.ps1
```

## 2. `.env`

```
LITELLM_HOST=127.0.0.1
LITELLM_PORT=8080
AI_GATEWAY_URL=http://127.0.0.1:8080
LITELLM_MASTER_KEY=sk-local-change-me
LITELLM_DATABASE_URL=postgresql://alexsoft:change-me@127.0.0.1:5432/litellm
DEEPSEEK_API_KEY=
# Optional Qwen:
# DASHSCOPE_API_KEY=
# DASHSCOPE_API_BASE=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

`setup-db.ps1` создаёт БД `litellm` и прописывает `LITELLM_DATABASE_URL` из `POSTGRES_*`.

## 3. Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\litellm\start-litellm.ps1
powershell -ExecutionPolicy Bypass -File infra\litellm\stop-litellm.ps1
```

`start-litellm.ps1` при занятом порте **сам останавливает** старый процесс и поднимает новый (чтобы подтянуть изменения `.env`, в т.ч. `LITELLM_MASTER_KEY`).

Admin UI: http://127.0.0.1:8080/ui — логин `admin`, пароль = значение `LITELLM_MASTER_KEY` из `.env`.  
Ошибка **Not connected to DB** = нет `LITELLM_DATABASE_URL` / БД `litellm` — снова `setup-db.ps1` и restart.

```powershell
curl.exe -s http://127.0.0.1:8080/health
```

## 4. Один запрос через шлюз

По умолчанию smoke бьёт в **DeepSeek**:

```powershell
powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-test.ps1
```

Qwen (если ключ DashScope есть):

```powershell
powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-test.ps1 -Model qwen
```

Или вручную:

```powershell
curl.exe -s http://127.0.0.1:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" `
  -d "{\"model\":\"deepseek\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hi in one word\"}]}"
```

Ожидается JSON с `choices[0].message.content`.

## Если не стартует

- Python / venv отсутствуют → снова `install-litellm.ps1`
- Порт занят → `Get-NetTCPConnection -LocalPort 8080`
- DeepSeek 401/invalid key → проверить `DEEPSEEK_API_KEY` и баланс на platform.deepseek.com
- Qwen 401/invalid key → проверить регион ключа и `DASHSCOPE_API_BASE`
- Системный SOCKS (Clash/V2Ray и т.п.) → `start-litellm.ps1` запускает через `run-proxy.py`, который отключает registry-proxy для процесса
- Логи → `%LOCALAPPDATA%\LiteLLM\litellm.out.log` и `litellm.err.log`

## Примечание про Windows Service

Пользовательский процесс, не служба. Автостарт — Task Scheduler на `start-litellm.ps1`, когда понадобится.

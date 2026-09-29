# n8n (native Windows)

Этап **5.4** — low-code оркестрация. LLM только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)).

## Где лежит на машине

| Компонент | Путь |
|-----------|------|
| npm prefix | `%LOCALAPPDATA%\AlexsoftN8n\prefix\` |
| Данные n8n | `%LOCALAPPDATA%\AlexsoftN8n\data\` |

| Сервис | URL |
|--------|-----|
| n8n GUI | http://127.0.0.1:5678 |
| LiteLLM | http://127.0.0.1:8080 |

## Установка

Нужен **Node.js 20.19–24.x**.

```powershell
powershell -ExecutionPolicy Bypass -File infra\n8n\install-n8n.ps1
```

## Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\n8n\start-n8n.ps1
powershell -ExecutionPolicy Bypass -File infra\n8n\stop-n8n.ps1
```

Опционально из корня: `scripts\dev-up.ps1 -WithN8n` / `dev-down.ps1 -WithN8n`.

## LiteLLM в UI

1. Откройте http://127.0.0.1:5678
2. **Credentials** → Add → **OpenAI** (или OpenAI-compatible, если есть)
3. **Base URL:** `http://127.0.0.1:8080/v1`
4. **API Key:** значение `LITELLM_MASTER_KEY` из `.env`
5. В нодах Chat/LLM укажите модель-алиас LiteLLM: `deepseek` (или `qwen`)

Не настраивайте прямые ключи DeepSeek / DashScope / OpenAI в n8n.

# Agent 1 (LangGraph stack)

Этап **5.2**: LangChain + LangGraph + LangSmith Studio + LangFlow.  
Все LLM-вызовы только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0012](../../artifacts/adr/0012-agent1-langgraph-stack.md)).

## Локально

Скрипты: [`infra/agent1/README.md`](../../infra/agent1/README.md).

| Сервис | URL |
|--------|-----|
| LiteLLM | http://127.0.0.1:8080 |
| Studio Agent Server | http://127.0.0.1:2024 |
| Studio UI | https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024 |
| LangFlow | http://127.0.0.1:7860 |

## Графы

- `graph.py` — echo без LLM (smoke Studio).
- `graph_llm.py` — chat через LiteLLM (`AGENT1_MODEL`, по умолчанию `deepseek`).
- `graph_qa.py` — **продукт: Q&A-агент с калькулятором** (см. ниже).

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\smoke-litellm.ps1
```

## Продукт: Q&A-агент с калькулятором

Граф `agent1_qa`: диалоговый ассистент, который отвечает на вопросы и выполняет расчёты
инструментом, а не «в уме». Вход — текст пользователя, выход — результат, выражение и разбор шагов.

Цикл: `agent` (LLM с tool `calculator`) → `tools` → `agent`, пока модели нужны вычисления.
Историю сообщений хранит `MessagesState`, поэтому «а умножь это на 3» относится к предыдущему
результату (в Studio — треды, в CLI — `MemorySaver` на время сессии).

Инструмент — `calculator.py`: выражение разбирается через `ast` и считается по белому списку
операторов, функций (`sqrt`, `log`, тригонометрия, `factorial`, ...) и констант (`pi`, `e`, `tau`).
`eval` не используется, переменные и любой другой код запрещены. Ошибки (деление на ноль, область
определения, неизвестная функция, синтаксис) возвращаются моделью пользователю понятным текстом.

CLI:

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1 --once "2^10 + sqrt(16)"
```

В Studio: `start-studio.ps1`, затем граф `agent1_qa` — в трейсе видно вызов `calculator` и
возврат в `agent`.

## Тот же продукт в LangFlow

Флоу `agent1_qa`: `Chat Input → Agent → Chat Output`, инструмент Agent'а — компонент
**Alexsoft Calculator**. Цикл «подумал → позвал инструмент → ответил» здесь внутри компонента
`Agent`, поэтому рёбер вида `agent → tools → agent` на канве нет, в отличие от графа LangGraph.
Контекст беседы держится по `session_id`.

Математика не продублирована: компонент
[`langflow/components/agent1/alexsoft_calculator.py`](langflow/components/agent1/alexsoft_calculator.py)
загружает `calculator.py` этого же каталога, а системный промпт и описание инструмента лежат в
[`prompts.py`](prompts.py) и используются обоими агентами. Правка `calculator.py` или `prompts.py`
меняет поведение сразу двух реализаций.

Сборка и прогон (LangFlow должен быть запущен):

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-build-qa-flow.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-ask.ps1 -Ask "37 от 128 в процентах"
```

Сборщик идемпотентен: пересоздаёт флоу с нуля и проверяет граф сборкой на сервере. После правки
компонента нужен `stop-langflow.ps1` + `start-langflow.ps1` (LangFlow читает файлы компонентов при
старте) и повторная сборка — в узле хранится копия кода.

Модель подключена через провайдер LangFlow **OpenAI Compatible**, который смотрит на LiteLLM:
`OPENAI_COMPATIBLE_BASE_URL` = `AI_GATEWAY_URL/v1` (задаёт `start-langflow.ps1`),
`OPENAI_COMPATIBLE_API_KEY` = `LITELLM_MASTER_KEY` (глобальная переменная LangFlow, её пишет
сборщик). Прямые ключи DeepSeek / DashScope в LangFlow не вводим — только через LiteLLM.

## LangFlow → git

Компоненты: [`langflow/components/`](langflow/components/) — код в репозитории, подключается
переменной `LANGFLOW_COMPONENTS_PATH` (её задаёт `start-langflow.ps1`).

Snapshots of your flows: [`langflow/flows/`](langflow/flows/).  
Enable once: `powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1` — then every `git commit` auto-exports and stages them.

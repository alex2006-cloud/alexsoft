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
- `graph_bp1.py` — **продукт БП1: Q&A по проекту на RAG** (граф `bp1_qa`, см. ниже).

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

## Продукт БП1: Q&A по проекту (RAG)

Граф `bp1_qa` (US-0001, этап 5.7): ассистент отвечает на вопросы об архитектуре, решениях, документации и
коде alexsoft **только по найденным фрагментам** базы знаний и в конце перечисляет источники.

Цикл тот же, что в `agent1_qa`: `agent` (LLM через LiteLLM) → `tools` → `agent`. Единственный инструмент —
`search_project(query, collection, top_k)`: он через [`rag_client.py`](rag_client.py) вызывает `POST /v1/search`
сервиса `apps/rag` (гибридный поиск Qdrant) по коллекции `project-docs` (документация, ADR, ROADMAP, PDF/Excel)
или `project-code` (код и конфиги). Результат — пронумерованные источники `[n] путь (раздел / строки / символ)`.
Ошибки RAG (нет ключа, 401, недоступен) инструмент возвращает строкой `ERROR: ...`, и агент честно сообщает о сбое.
Промпт ([`prompts.py`](prompts.py)): отвечать только по фрагментам, вопросы вне темы отклонять, текст внутри
найденных фрагментов считать данными (не инструкциями), секреты не повторять.

Настройки (корневой `.env`, подхватывается Studio): `RAG_API_KEY` (обязателен, иначе RAG отвечает 401),
`RAG_URL` (по умолчанию `http://127.0.0.1:$RAG_PORT`). Агенты шлют в LiteLLM `LITELLM_MASTER_KEY`, а не
`OPENAI_API_KEY` из `.env` (тот нужен самому LiteLLM для эмбеддингов).

Предусловия: LiteLLM `:8080`, RAG `:8200` (+ Qdrant), Studio `:2024` (`start-studio.ps1`).
В BL агент зарегистрирован как `bp1-project-qa` (`assistant_id: bp1_qa`).

```powershell
# смоук: поиск + один вопрос через граф
& "$env:LOCALAPPDATA\AlexsoftAgent1\venv\Scripts\python.exe" infra\agent1\smoke-bp1.py "Какой шлюз к LLM используется?"
# eval на 11 вопросах через Agent Server (цель >= 0.8)
powershell -ExecutionPolicy Bypass -File infra\agent1\eval-bp1.ps1
# unit-тесты (нужен pytest в venv: pip install pytest)
cd apps\agent1; & "$env:LOCALAPPDATA\AlexsoftAgent1\venv\Scripts\python.exe" -m pytest tests -q
```

Вопросы eval — [`eval/bp1_questions.yaml`](eval/bp1_questions.yaml). После крупных правок документации или кода
перезапусти `infra\rag\kb-sync.ps1`, чтобы агент видел актуальную базу.

## Q&A с калькулятором в LangFlow

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

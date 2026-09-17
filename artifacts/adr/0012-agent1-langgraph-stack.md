# ADR-0012: Agent 1 = LangGraph stack (native Windows)

- **Статус:** accepted
- **Дата:** 2026-09-17
- **Контекст:** Этап 5.2 — первый AI-агент после AI Gateway (LiteLLM, [ADR-0011](0011-ai-gateway-litellm.md)). Нужны оркестрация графа, IDE отладки и визуальный конструктор; все вызовы моделей — только через LiteLLM. Не путать **LangSmith Studio** (IDE) с **LangSmith** платформой трейсов (этап 5.6).
- **Решение:**
  - **Стек агента 1:** LangChain + **LangGraph** + **LangSmith Studio** (`langgraph-cli[inmem]` / `langgraph dev`) + **LangFlow**.
  - **Где:** нативно на Windows. Venv Agent1: `%LOCALAPPDATA%\AlexsoftAgent1\`; LangFlow отдельно: `%LOCALAPPDATA%\LangFlow\`. Скрипты: `infra/agent1/`. Код графа: `apps/agent1/`.
  - **Порты (loopback):** Studio Agent Server **2024**, LangFlow **7860**, LiteLLM **8080**.
  - **LLM:** OpenAI-compatible клиент → `AI_GATEWAY_URL/v1`, ключ `LITELLM_MASTER_KEY`, модель `AGENT1_MODEL` (по умолчанию `deepseek`). Прямых вызовов DeepSeek / DashScope / OpenAI из агента нет.
  - **Studio GUI:** `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`; для UI нужен `LANGSMITH_API_KEY`. Трейсинг по умолчанию выключен (`LANGSMITH_TRACING=false`) до этапа 5.6.
  - **LangFlow:** OpenAI-compatible endpoint на LiteLLM (тот же base URL / key / model).
  - **AI-продукт** (пост / тестировщик / каналы) и ссылка с Lab — отдельные задачи ROADMAP после этой связки.
- **Последствия:**
  - Инструкции: `infra/agent1/README.md`, `apps/agent1/README.md`.
  - Structurizr: контейнер Agent 1 → AI Gateway.
  - Следующие агенты (CrewAI, AutoGen) также обязаны ходить только через LiteLLM.

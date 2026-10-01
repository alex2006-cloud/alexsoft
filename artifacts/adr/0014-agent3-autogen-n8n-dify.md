# ADR-0014: Agent 3 = AutoGen; n8n + Dify in AI contour

- **Статус:** accepted
- **Дата:** 2026-09-18
- **Контекст:** Этап 5.4 — третий AI-агент после LangGraph ([ADR-0012](0012-agent1-langgraph-stack.md)) и CrewAI ([ADR-0013](0013-agent2-crewai.md)). Нужны conversation/group-chat multi-agent (AutoGen) и low-code оркестрация (n8n, Dify). Все вызовы моделей — только через LiteLLM ([ADR-0011](0011-ai-gateway-litellm.md)). На ноутбуке по умолчанию — нативные установки; Dify официально рекомендует Docker Compose.
- **Решение:**
  - **Стек агента 3:** Microsoft **AutoGen AgentChat** (`autogen-agentchat` + `autogen-ext[openai]`). Клиент: `OpenAIChatCompletionClient` → OpenAI-compatible `AI_GATEWAY_URL/v1`, ключ `LITELLM_MASTER_KEY`, модель = алиас LiteLLM (`AGENT3_MODEL`, по умолчанию `deepseek`) с явным `model_info` (не openai-hosted имя).
  - **Где (AutoGen):** нативно на Windows. Venv: `%LOCALAPPDATA%\AlexsoftAgent3\`. Скрипты: `infra/agent3/`. Код: `apps/agent3/`. UI: CLI smoke. Отдельный «продукт агента 3» не входит в 5.4; первый AI-агент с RAG — после Architecture and documentation и RAG-сервиса (ROADMAP 5.5 → 5.6 → 5.7).
  - **n8n:** нативно (Node.js + локальный npm в `%LOCALAPPDATA%\AlexsoftN8n\`). GUI: `http://127.0.0.1:5678`. LLM: OpenAI credential → LiteLLM.
  - **Dify:** **осознанное Docker-исключение** на этапе 5 (Compose из upstream `langgenius/dify`). Clone: `%LOCALAPPDATA%\AlexsoftDify\`. GUI: `http://127.0.0.1:3003` (`EXPOSE_NGINX_PORT`, не 3000 — лендинг). Из контейнеров к LiteLLM на хосте: `http://host.docker.internal:8080/v1`.
  - **Vs LangGraph / CrewAI:** агент 1 — явный граф состояний + tools; агент 2 — роли/задачи sequential crew; агент 3 — conversation / multi-agent chat (AgentChat). n8n и Dify — low-code оркестрация рядом с агентами, не замена agent numbers. Все обязаны ходить только через LiteLLM.
- **Последствия:**
  - Инструкции: `infra/agent3/README.md`, `infra/n8n/README.md`, `infra/dify/README.md`, `apps/agent3/README.md`.
  - Structurizr: Agent 3, n8n, Dify → AI Gateway.
  - `dev-up` / `dev-down`: опциональные флаги `-WithN8n` / `-WithDify` (не поднимать Docker Dify по умолчанию).
  - Первый AI-агент с RAG — ROADMAP **5.7**, после **5.5** (docs) и **5.6** (RAG). Продукт агента 3 как отдельный шаг 5.4 — отменён.

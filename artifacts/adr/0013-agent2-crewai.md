# ADR-0013: Agent 2 = CrewAI (native Windows)

- **Статус:** accepted
- **Дата:** 2026-09-18
- **Контекст:** Этап 5.3 — второй AI-агент после LangGraph ([ADR-0012](0012-agent1-langgraph-stack.md)). Нужна оркестрация ролей/задач (multi-agent crew) для продукта «черновик поста»; все вызовы моделей — только через LiteLLM ([ADR-0011](0011-ai-gateway-litellm.md)). Официального локального GUI у open-source CrewAI нет (в отличие от LangSmith Studio / LangFlow у агента 1).
- **Решение:**
  - **Стек агента 2:** **CrewAI** (`Crew` + `Agent` + `Task`, `Process.sequential`).
  - **Где:** нативно на Windows. Venv: `%LOCALAPPDATA%\AlexsoftAgent2\`. Скрипты: `infra/agent2/`. Код: `apps/agent2/`.
  - **LLM:** `crewai.LLM` → OpenAI-compatible `AI_GATEWAY_URL/v1`, ключ `LITELLM_MASTER_KEY`, модель `openai/{AGENT2_MODEL}` (по умолчанию `openai/deepseek`). Прямых вызовов DeepSeek / DashScope / OpenAI из агента нет. Не использовать `crewai[litellm]` как обход шлюза alexsoft.
  - **UI:** CLI (`run-post.ps1`). Community CrewAI-Studio / Enterprise Crew Studio — вне этого ADR.
  - **Продукт:** черновик поста — Researcher → Writer → Editor → итоговый текст (детали сценария уточняются позже).
  - **Vs LangGraph:** агент 1 — явный граф состояний + tools; агент 2 — роли и задачи с последовательной передачей контекста. Оба обязаны ходить только через LiteLLM.
- **Последствия:**
  - Инструкции: `infra/agent2/README.md`, `apps/agent2/README.md`.
  - Structurizr: контейнер Agent 2 → AI Gateway.
  - Следующий агент (AutoGen, этап 5.4) также только через LiteLLM.

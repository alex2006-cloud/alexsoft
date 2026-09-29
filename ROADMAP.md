# Дорожная карта

Порядок соответствует этапам реализации. Не перескакивать инфраструктурные зависимости без необходимости.

## Этап 0 — каркас (готово)

- [x] Структура монорепозитория
- [x] Папка артефактов + Structurizr C4 L1
- [x] `.env.example`
- [x] GitHub remote + первый push (`alex2006-cloud/alexsoft`)
- [x] Локальный `.env` (не в git)

## Этап 1 — публичный контур (готово)

- [x] Лендинг (Next.js): страница, портфолио, кнопки на сервисы
- [x] Домен + DNS (`osipcraft.ru`, хостинг Hostline, VPS Fornex)
- [x] GitHub Actions: сборка лендинга
- [x] GitHub Actions: экспорт Structurizr (PNG/SVG) при push

## Этап 2 — платформа данных (готово)

- [x] PostgreSQL — локально (нативная установка Windows, ADR-0004); VPS/облако позже
- [x] Redis — локально (Memurai / Windows, ADR-0005); VPS/облако позже
- [x] MinIO — локально (нативный `minio.exe` + Console, ADR-0006); VPS/облако позже

## Этап 3 — observability и BI (готово)

На Windows — нативно и по одному компоненту. Docker/Compose — на этапе VPS, не в этой нитке.

**Observability**

- [x] Loki (native) — хранение логов
- [x] Prometheus (native) — хранение метрик
- [x] Grafana Alloy (native) — агент сбора
- [x] Grafana (native) — UI (порт ≠ 3000, лендинг)
- [x] Alloy: один поток логов → Loki, одна метрика → Prometheus
- [x] Просмотр в Grafana (логи и метрики)
- [x] ADR + README + порты в `.env` / `.env.example`

**BI (после observability)**

- [x] Metabase поверх PostgreSQL (native) — [ADR-0009](artifacts/adr/0009-metabase-native-local.md)
- [x] Один отчёт / вопрос в Metabase (`demo_items`)

## Этап 4 — игры как продукт (готово)

Без Docker. Статика в браузере; деплой вместе с лендингом. См. [ADR-0010](artifacts/adr/0010-games-static-app.md).

- [x] Мини-игра «Контур» (C4 Puzzle)
- [x] Каталог `/games` и страницы игр (Десант, Вайб-чек)
- [x] Карточка «Игры» в блоке лаборатории → каталог
- [x] Вынос в `apps/games` + CI merge со статикой лендинга (вариант B)

## Этап 5 — AI-контур (текущий)

По [CONCEPT.md](CONCEPT.md).  
**AI Gateway = LiteLLM** (не путать с API Gateway / IAM — этап 6). Облачные LLM: **DeepSeek** (подключён), Qwen (в конфиге). Три агента подряд, у каждого свой продукт; затем синхронизация архитектуры/доков → RAG → LangSmith.  
**LangSmith Studio** (IDE графа; бывш. LangGraph Studio) ≠ **LangSmith** (платформа трейсов/evals).  
Публичный демо-чат с лендинга **не** выкладываем до API Gateway / IAM (этап 6) — иначе расход токенов и утечка ключей.  
**Redis-кеш ответов AI и RabbitMQ** — не в этапе 5; ставим при **целевой архитектуре** (облако / этап 6). Memurai с этапа 2 для данных остаётся как есть.

**5.1 — AI Gateway + LLM**

- [x] LiteLLM (локально)
- [x] Подключить **DeepSeek** (`deepseek` → `deepseek/deepseek-chat`, ключ `DEEPSEEK_API_KEY`) — рабочий провайдер
- [x] Алиас **Qwen** в конфиге (`qwen` → `dashscope/qwen-plus`; ключ `DASHSCOPE_API_KEY` — по мере надобности)
- [x] Ключ DeepSeek в `.env`, проверка запроса через шлюз
- [x] ADR: AI Gateway = LiteLLM ([ADR-0011](artifacts/adr/0011-ai-gateway-litellm.md))

**5.2 — агент 1 (LangGraph) + продукт**

- [x] LangChain / LangGraph + LangSmith Studio (IDE; бывш. LangGraph Studio) + LangFlow (через LiteLLM)
- [x] AI-продукт через агент 1: **Q&A-агент с калькулятором** (граф `agent1_qa`, tool `calculator`, память сессии) — локально (`infra/agent1/chat-qa.ps1`, Studio) — [`apps/agent1`](apps/agent1/README.md)
- [x] Тот же продукт в LangFlow: флоу `agent1_qa` + компонент Alexsoft Calculator поверх того же `calculator.py` (`infra/agent1/langflow-build-qa-flow.ps1`, `langflow-ask.ps1`)
- [x] ADR: агент 1 = LangGraph-стек ([ADR-0012](artifacts/adr/0012-agent1-langgraph-stack.md))

**5.3 — агент 2 (CrewAI) + продукт**

- [x] CrewAI через LiteLLM
- [x] AI-продукт через агент 2: **черновик поста** (Researcher → Writer → Editor) — локально (`infra/agent2/run-post.ps1`) — [`apps/agent2`](apps/agent2/README.md)
- [x] ADR: CrewAI vs LangGraph ([ADR-0013](artifacts/adr/0013-agent2-crewai.md))

**5.4 — AutoGen + n8n + Dify → затем агент 3 / продукт**

Сначала стек, потом продукт агента 3 (не раньше, чем установлены AutoGen, n8n и Dify).

- [x] AutoGen через LiteLLM — локально (`infra/agent3/install-autogen.ps1`, `smoke-litellm.ps1`) — [`apps/agent3`](apps/agent3/README.md)
- [x] **n8n** (локально npm; LLM только через LiteLLM) — GUI `:5678` (`infra/n8n`)
- [x] **Dify** (Docker Compose на ноутбуке; LLM только через LiteLLM) — GUI `:3003` (`infra/dify`)
- [x] ADR: AutoGen vs LangGraph / CrewAI; роль n8n и Dify ([ADR-0014](artifacts/adr/0014-agent3-autogen-n8n-dify.md))
- [ ] AI-продукт через агент 3 (только после пунктов выше)

**5.5 — Architecture and documentation**

Синхронизация артефактов после стека 5.1–5.4 (агент Cursor **Architecture and documentation**), **до** RAG.

- [ ] Создать документы по бизнес кейсу 1: User Stories (Бизнес-кейс 1), Use Cases (Бизнес-кейс 1) в виде спецификации и диаграммы, BPMN (Бизнес-кейс 1), Sequence Diagram (Бизнес-кейс 1)
- [ ] Создать документы по системе: Component Diagram всей системы, C4 — 1,2,3 уровень,  API-контракт (OpenAPI) для RAG-системы
- [ ] Актуализировать `artifacts/structurizr/workspace.dsl` под архитектуру всей системы
- [ ] Дописать / проверить ADR (в т.ч. пробелы относительно текущего стека)
- [ ] Выровнять `CONCEPT.md`, `ROADMAP.md`, `AGENTS.md`, корневой `README.md` и README сервисов
- [ ] Экспорт диаграмм / проверка, что C4 отражает фактический контур

**5.6 — векторная БД + RAG + продукт с RAG**

- [ ] Выбор ВБД: Qdrant **или** Weaviate (ADR)
- [ ] RAG, 3 слоя: загрузка → хранение эмбеддингов → пайплайны поиска (LangChain / LlamaIndex — ADR)
- [ ] `apps/rag` + AI-продукт **с RAG**
- [ ] Lab «RAG» → Live (когда есть URL)

**5.7 — LangSmith (платформа, не Studio)**

- [ ] Довести LangSmith (платформа): трейсы, анализ, оценка прогонов — не путать с LangSmith Studio
- [ ] Зафиксировать: Loki/Grafana ≠ LangSmith (платформа) ≠ LangSmith Studio (IDE)

## Этап 6 — облако и комплаенс (целевая архитектура)

Сначала обсуждение «что переносим». Затем по CONCEPT:

- [ ] Архитектура переноса (Structurizr / ADR)
- [ ] API Gateway (инструмент — уточнить)
- [ ] IAM (инструмент — уточнить)
- [ ] SSH, Docker на VDS (+ опционально Portainer)
- [ ] Redis вместо Memurai; **Redis-кеш ответов AI**; Postgres/MinIO в облаке; туннели к DBeaver / Console
- [ ] **RabbitMQ** — очередь долгих AI-задач (+ ADR, порты в `.env` / README)
- [ ] Observability и Metabase на VDS (по необходимости)
- [ ] k3s
- [ ] Kafka (если понадобится сверх RabbitMQ)
- [ ] Заявка в РКН как оператор ПДн — только если появятся ПДн субъектов РФ в проде

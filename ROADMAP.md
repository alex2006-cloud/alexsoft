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
**AI Gateway = LiteLLM** (не путать с API Gateway / IAM — этап 6). Облачные LLM: **DeepSeek** (подключён), Qwen (в конфиге).  
Порядок: 5.1–5.3 (шлюз + агенты с продуктами) → **5.4 стек агентов** (lab, **без** продукта агента 3) → **5.5** архитектура и документация → **5.6** ВБД + RAG → **5.7** первый AI-агент с RAG.  
**LangSmith Studio** (IDE графа; бывш. LangGraph Studio) ≠ **LangSmith** (платформа трейсов/evals; в этапе 5 отдельным шагом не ведём).  
Публичный демо-чат с лендинга **не** выкладываем до API Gateway / IAM (этап 6) — иначе расход токенов и утечка ключей.  
**Redis-кеш ответов AI и RabbitMQ** — не в этапе 5; ставим при **целевой архитектуре** (облако / этап 6). Memurai с этапа 2 для данных остаётся как есть. До брокера FastAPI вызывает Agent Platform напрямую (временная связь, [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)).  
Агенты 2–3 и n8n (5.3–5.4) — lab этапа 5; в целевую архитектуру ([ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)) не входят.

**5.1 — AI Gateway + LLM**

- [x] LiteLLM (локально)
- [x] Подключить **DeepSeek** (`deepseek` → `deepseek/deepseek-chat`, ключ `DEEPSEEK_API_KEY`) — рабочий провайдер
- [x] Алиас **Qwen** в конфиге (`qwen` → `dashscope/qwen-plus`; ключ `DASHSCOPE_API_KEY` — по мере надобности)
- [x] Ключ DeepSeek в `.env`, проверка запроса через шлюз
- [x] ADR: AI Gateway = LiteLLM ([ADR-0011](artifacts/adr/0011-ai-gateway-litellm.md))

**5.2 — агент 1 (LangGraph) + продукт**

- [x] LangChain / LangGraph + LangSmith Studio (IDE; бывш. LangGraph Studio) + LangFlow (через LiteLLM)
- [x] AI-продукт через агент 1: **Q&A-агент с калькулятором** (граф `agent1_qa`, tool `calculator`, память сессии) — локально (`infra/agent1/chat-qa.ps1`, Studio) — `[apps/agent1](apps/agent1/README.md)`
- [x] Тот же продукт в LangFlow: флоу `agent1_qa` + компонент Alexsoft Calculator поверх того же `calculator.py` (`infra/agent1/langflow-build-qa-flow.ps1`, `langflow-ask.ps1`)
- [x] ADR: агент 1 = LangGraph-стек ([ADR-0012](artifacts/adr/0012-agent1-langgraph-stack.md))

**5.3 — второй агент + продукт (lab, выполнено)**

- [x] CrewAI через LiteLLM
- [x] AI-продукт через агент 2: **черновик поста** (Researcher → Writer → Editor) — локально (`infra/agent2/run-post.ps1`) — `[apps/agent2](apps/agent2/README.md)`
- [x] ADR: CrewAI vs LangGraph ([ADR-0013](artifacts/adr/0013-agent2-crewai.md))

**5.4 — стек агентов (lab, выполнено; в целевой остаётся Dify)**

Только установка и ADR. Продукт агента 3 и первый AI-агент с RAG — **не** здесь: после **5.5** → **5.6** (RAG) → **5.7** (агент с RAG).

- [x] AutoGen через LiteLLM — локально (`infra/agent3/install-autogen.ps1`, `smoke-litellm.ps1`) — `[apps/agent3](apps/agent3/README.md)`
- [x] **n8n** (локально npm; LLM только через LiteLLM) — GUI `:5678` (`infra/n8n`)
- [x] **Dify** (Docker Compose на ноутбуке; LLM только через LiteLLM) — GUI `:3003` (`infra/dify`)
- [x] ADR: AutoGen vs LangGraph / CrewAI; роль n8n и Dify ([ADR-0014](artifacts/adr/0014-agent3-autogen-n8n-dify.md))

**5.5 — Architecture and documentation**

Синхронизация артефактов после стека 5.1–5.4 (агент Cursor **Architecture and documentation**), **до** RAG (**5.6**) и первого AI-агента с RAG (**5.7**).

- [x] Создать документы по бизнес кейсу 1: User Stories (Бизнес-кейс 1), Use Cases (Бизнес-кейс 1) в виде спецификации и диаграммы, BPMN (Бизнес-кейс 1), Sequence Diagram (Бизнес-кейс 1) — [`artifacts/business-cases/bc1/`](artifacts/business-cases/bc1/)
- [x] Создать архитектуру в drawio и утвердить стеки технологий ([`architecture-in-drawio.drawio`](artifacts/architecture/architecture-in-drawio.drawio), [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md))
- [x] Актуализировать `artifacts/architecture/c4-l1-l2-l3.dsl` (C4 — 1,2,3 уровень) под целевую архитектуру ([`architecture-in-drawio.drawio`](artifacts/architecture/architecture-in-drawio.drawio), [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md))
- [x] Создать Component Diagram всей системы ([`uml-component-diagram.puml`](artifacts/architecture/uml-component-diagram.puml))
- [x] API-контракт (OpenAPI) для RAG-системы — `artifacts/api/rag.openapi.yaml`
- [x] Дописать / проверить ADR (целевая архитектура и стеки — [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md); выравнивание остальных доков — ниже)
- [x] Выровнять `CONCEPT.md`, `ROADMAP.md`, `AGENTS.md`, корневой `README.md` и README сервисов
- [x] Экспорт диаграмм — [`artifacts/generated/`](artifacts/generated/) (C4 PNG/SVG + UML Component)

**5.6 — векторная БД + RAG**

После закрытия **5.5**. Инфра RAG без продукта-агента.

- [x] Выбор ВБД: **Qdrant** ([ADR-0015](artifacts/adr/0015-target-architecture-stacks.md); Weaviate отклонён для целевого контура)
- [x] RAG-стек: **LlamaIndex** + hybrid в Qdrant; embedding **`text-embedding-3-small`** через LiteLLM ([ADR-0015](artifacts/adr/0015-target-architecture-stacks.md))
- [x] Qdrant — локально (нативный `qdrant.exe`, [`infra/qdrant`](infra/qdrant/README.md), [ADR-0017](artifacts/adr/0017-rag-service-implementation.md))
- [x] LiteLLM: алиас `text-embedding-3-small` в `infra/litellm/config.yaml` (нужен `OPENAI_API_KEY` в `.env`)
- [x] RAG, 3 слоя в коде: загрузка → хранение эмбеддингов → пайплайны поиска (hybrid dense+BM25, RRF/DBSF)
- [x] `apps/rag` (сервис RAG, FastAPI, порт 8200; реализует `rag.openapi.yaml`; тесты: unit + интеграционные + контрактные) — `[apps/rag](apps/rag/README.md)`
- [x] Мультиформатный ingest и **база знаний о проекте** (docs + код): PDF (+ vision-OCR сканов через LiteLLM), Excel (таблицы + формулы), код (символы и строки), `.bpmn`/`.drawio`; коллекции `project-docs` и `project-code`; `infra/rag/kb-sync.ps1` (инкрементально, с защитой от секретов и LLM-описаниями файлов) — [ADR-0018](artifacts/adr/0018-rag-multiformat-ingest-and-project-kb.md)
- [ ] Живой прогон на `text-embedding-3-small`: ключ `OPENAI_API_KEY` в `.env` → перезапуск LiteLLM → `infra/litellm/smoke-embeddings.ps1` → `infra/rag/kb-sync.ps1` → `apps/rag/eval/run_eval.py --answer`

**5.7 — первый AI-агент с RAG**

После **5.6**. Первый AI-продукт с RAG (см. БК1); не путать с «продуктом агента 3» из старого плана 5.4.

- [ ] **Первый AI-агент с RAG** (поверх `apps/rag` + LiteLLM)
- [ ] Lab «RAG» → Live (когда есть URL; публично — только после IAM, этап 6)

## Этап 6 — облако и комплаенс (целевая архитектура)

Сначала обсуждение «что переносим». Затем по CONCEPT:

- [ ] Архитектура переноса (Structurizr / ADR)
- [ ] Edge / reverse proxy: **Nginx** (+ NPM при RAM/Docker) — стек утверждён ([ADR-0007](artifacts/adr/0007-edge-nginx-npm.md), [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)); внедрение на целевом VDS
- [ ] IAM: **Authentik** — стек утверждён ([ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)); внедрение на целевом VDS
- [ ] SSH, Docker на VDS (+ опционально Portainer)
- [ ] Redis вместо Memurai; **Redis-кеш ответов AI**; Postgres/MinIO в облаке; туннели к DBeaver / Console
- [ ] **FastAPI** — BL API (оркестрация сценариев, публикация запуска агента); **LLM Guard** — guardrails перед/после LiteLLM
- [ ] **RabbitMQ** — очередь запуска агентов (publish от FastAPI, consume на Agent Platform) (+ ADR, порты в `.env` / README); убрать временную прямую связь BL → Agent Platform из C4 / Component Diagram / ADR-0015
- [ ] Observability и Metabase на VDS (по необходимости)
- [ ] k3s
- [ ] Kafka (если понадобится сверх RabbitMQ)
- [ ] Заявка в РКН как оператор ПДн — только если появятся ПДн субъектов РФ в проде
# ADR-0015: Целевая архитектура alexsoft и утверждённые стеки

- **Статус:** accepted
- **Дата:** 2026-10-01
- **Контекст:** Этап **5.5** (Architecture and documentation). Нужен единый утверждённый снимок **целевой** runtime-архитектуры платформы (не MVP-срез) и фиксация стеков, выбранных при проектировании в draw.io. Источник C4 по-прежнему Structurizr ([ADR-0001](0001-architecture-as-code.md)); draw.io — согласованная топологическая схема целевого контура. Часть компонентов уже принята отдельными ADR (edge, данные, observability, BI, LiteLLM, агенты 1–3); этот ADR **сводит картину**, закрывает пробелы (IAM, BL, RAG/ВБД/embeddings, guardrails, брокер в целевой схеме, delivery) и фиксирует решения по БК1.

- **Рассмотренные альтернативы (сводка выборов):**
  - **Edge / «API Gateway» на схеме:** Kong / Traefik / отдельный API GW — отклонены для текущего целевого контура; **Nginx** (+ позже NPM) как reverse proxy / TLS / маршрутизация ([ADR-0007](0007-edge-nginx-npm.md)).
  - **IAM:** Keycloak / Auth0 / самопис — отклонены; **Authentik** (self-host, OIDC/JWT).
  - **Бизнес-логика API:** Node/Nest, Go — отложены; **FastAPI (Python)** — единый язык с AI/RAG-контуром.
  - **AI Gateway:** прямой вызов провайдеров из агентов — запрещён; только **LiteLLM** ([ADR-0011](0011-ai-gateway-litellm.md)).
  - **ВБД:** Weaviate — запасной вариант CONCEPT/старых черновиков; целевой выбор — **Qdrant** (hybrid retrieval).
  - **RAG-фреймворк:** LangChain-only пайплайн — не выбран как основной RAG-слой; **LlamaIndex** (load / clean / chunk / retrieve). LangChain остаётся в контуре агента 1, не как канон RAG-сервиса.
  - **Embeddings:** локальные / DeepSeek embeddings — нет публичного API у DeepSeek; выбран облачный **`text-embedding-3-small` через LiteLLM** (шлюз ≠ модель).
  - **Guardrails:** NVIDIA NeMo Guardrails и др. — не выбраны; **LLM Guard**.
  - **Брокер:** Kafka — рано для масштаба lab; **RabbitMQ** в **целевой** схеме (долгие AI-задачи); установка/проводка — не блокер локального ИИ этапа 5 (см. ROADMAP этап 6).
  - **Кэш:** Memurai локально ([ADR-0005](0005-redis-native-local.md)); на схеме целевой — **Redis** (в т.ч. кеш ответов AI — этап 6).
  - **Agent Platform на целевой схеме:** полный перечень лабораторных агентов (CrewAI, AutoGen, n8n) не дублируется отдельными боксами. На draw.io зафиксированы **две целевые платформы:** (1) код — LangGraph + LangSmith Studio + LangFlow; (2) UI без кода — **Dify**. CrewAI / AutoGen / n8n остаются в этапном контуре обучения/стека ([ADR-0013](0013-agent2-crewai.md), [ADR-0014](0014-agent3-autogen-n8n-dify.md)); **n8n** на целевой диаграмме **не обязателен** (можно добавить позже).
  - **Облачные LLM:** DeepSeek, Qwen, ChatGPT, **Claude**, **Gemini** — перечень CONCEPT; доступ только через LiteLLM.

- **Решение:**

  ### Артефакт
  - Утверждённая целевая схема: [`artifacts/architecture/architecture-in-drawio.drawio`](../architecture/architecture-in-drawio.drawio).
  - Диаграмма описывает **целевой** контур (VPS/сервер + delivery), без отдельной «MVP-only» ветки на той же картинке.

  ### Периметр и приложения
  | Роль | Стек |
  |------|------|
  | Edge / веб-сервер / reverse proxy | **Nginx** (+ **Nginx Proxy Manager** при достаточном RAM / Docker) |
  | IAM | **Authentik** (OIDC; JWT проверяет FastAPI по JWKS, не Nginx — [ADR-0019](0019-cabinet-ssr-bff-authentik.md)) |
  | Frontend (лендинг и игры) | **Next.js**, статика SSG; раздаёт Nginx ([ADR-0010](0010-games-static-app.md), [ADR-0019](0019-cabinet-ssr-bff-authentik.md)) |
  | Frontend (кабинет, админка) | **Next.js SSR (Node) + BFF**, `apps/cabinet` ([ADR-0019](0019-cabinet-ssr-bff-authentik.md)) |
  | Бизнес-логика (API) | **FastAPI (Python)** |

  ### Данные и интеграционная шина (целевая схема)
  | Роль | Стек |
  |------|------|
  | РСУБД | **PostgreSQL** |
  | Объектное хранилище | **MinIO** |
  | Векторная БД | **Qdrant** |
  | Кэш | **Redis** (локально этап 2 — Memurai) |
  | Брокер сообщений | **RabbitMQ** |

  ### ИИ-контур
  | Роль | Стек |
  |------|------|
  | AI Gateway | **LiteLLM** |
  | Облачные LLM | DeepSeek, Qwen, ChatGPT, Claude, Gemini (алиасы в LiteLLM) |
  | Embedding-модель | **`text-embedding-3-small`** через LiteLLM (индексация и query embedding) |
  | Agent Platform (код) | **LangGraph** + **LangSmith Studio** + **LangFlow** ([ADR-0012](0012-agent1-langgraph-stack.md)) |
  | Agent Platform (UI) | **Dify** ([ADR-0014](0014-agent3-autogen-n8n-dify.md); Compose на ноутбуке — исключение) |
  | RAG-слой | **LlamaIndex** (load / clean / chunk / retrieve); hybrid search в **Qdrant** |
  | Guardrails | **LLM Guard** (sync pre/post вокруг вызовов моделей) |
  | LLM traces / evals | **LangSmith** (платформа; не путать со Studio) |

  ### Наблюдаемость и BI
  | Роль | Стек |
  |------|------|
  | Метрики | **Prometheus** |
  | Логи | **Loki** + агент **Grafana Alloy** |
  | Дашборды инфры | **Grafana** ([ADR-0008](0008-observability-native-local.md)) |
  | BI | **Metabase** ([ADR-0009](0009-metabase-native-local.md)) |

  ### Поставка и секреты
  - Цепочка: **Cursor → GitHub (monorepo) → GitHub Actions → VDS/VPS**.
  - На сервере не правят руками то, что должно приходить из CI.
  - Секреты **вне git** (локально `.env`; в CI — GitHub Secrets). В репозитории только `.env.example`.

  ### Потоки (канон для БК1 и целевой схемы)
  - Клиент → Nginx → статика (лендинг, игры) **или** кабинет Next.js SSR (`reverse proxy /app, /api`) → FastAPI (REST + SSE статуса). Вход: Nginx проксирует на Authentik; кабинет обменивает код на токены (OIDC); FastAPI проверяет JWT по JWKS Authentik ([ADR-0019](0019-cabinet-ssr-bff-authentik.md)).
  - **Целевой (этап 6):** FastAPI публикует запуск агента в **RabbitMQ** (`publish`); **Agent Platform** забирает задачу (`consume run`) — как на схеме «Архитектура 8».
  - **Этап 5 (решение владельца: брокер на старте не нужен):** FastAPI вызывает Agent Platform напрямую по HTTPS; RabbitMQ не ставится. Прямая связь BL → Agent Platform — временная, добавлена в C4 и Component Diagram сверх XML 8 и удаляется при внедрении брокера.
  - **RAG** читает документы из **MinIO**, пишет/ищет векторы в **Qdrant**, ходит в LiteLLM за embeddings и (при необходимости) LLM.
  - **Agent Platform** и **RAG** вызывают модели **только через LiteLLM**; прямых ключей провайдеров в агентах/RAG нет.
  - **LLM Guard** — на пути agent/RAG ↔ LiteLLM (pre/post).
  - Связь **BL → LiteLLM** на схеме оставлена намеренно (задел под будущие продукты), не как обязательный путь БК1 day-one. Связь **Broker → LiteLLM** заменена на **Broker → Agent Platform (`consume run`)**.
  - Agent Platform и RAG ходят в LiteLLM напрямую (`OpenAI-compatible`, `embeddings + LLM`) и, параллельно, через LLM Guard (`sync pre/post check`).
  - Инфра-метрики/логи → Alloy / Prometheus / Loki → Grafana; LLM-прогоны → LangSmith; продуктовая аналитика БД → Metabase.

  ### Бизнес-кейс 1 (границы успеха)
  - Сторонний пользователь: лендинг → логин (IAM) → список агентов → Q&A-агент по проекту.
  - Критерий успеха контура: **прогон агента + trace + результат** (ответ с опорой на корпус).
  - Корпус для первого RAG: документы проекта (ручной / batch ingest в MinIO → LlamaIndex → Qdrant); hybrid retrieval.

  ### Этапность vs целевая схема
  - **Архитектура первична:** ROADMAP нарезает внедрение, а не отодвигает утверждённые узлы «на VPS». **Authentik и личный кабинет** поднимаем **локально** по этой схеме, не дожидаясь переноса.
  - Локальный этап 5 **не обязан** поднять Redis AI-cache и RabbitMQ до продуктов агентов/RAG. В целевой схеме запуск агента идёт через RabbitMQ; до брокера локально допустим прямой вызов агента.
  - Полноценный edge с JWT в проде, Redis AI-cache, RabbitMQ на сервере — **целевой контур**; этап 6 ROADMAP — **планирование** переноса/создания заново, без детального чеклиста внедрения.
  - Лабораторные агенты CrewAI / AutoGen и n8n не отменяются предыдущими ADR; на целевой draw.io они не обязаны быть отдельными узлами.

- **Последствия:**
  - Считать стеки выше **источником правды для целевой топологии**; смена узла (IAM, ВБД, RAG-фреймворк, guardrails, BL) — новый ADR или supersede этого.
  - Закрыты развилки ROADMAP **5.6** по выбору: ВБД = **Qdrant**; RAG-фреймворк = **LlamaIndex**; embedding = **text-embedding-3-small via LiteLLM**. Реализация `apps/rag` и установка Qdrant — отдельные задачи 5.6, не этот ADR.
  - ROADMAP **5.5**: пункт «создать архитектуру в drawio и утвердить стеки» — выполнен этим ADR + файлом drawio.
  - Далее в 5.5: синхронизировать `artifacts/architecture/c4-l1-l2-l3.dsl`, [`uml-component-diagram.puml`](../architecture/uml-component-diagram.puml), CONCEPT/ROADMAP/AGENTS/README (убрать «Qdrant или Weaviate», «LangChain / LlamaIndex уточнить», IAM/API GW «TBD» где устарело).
  - Не плодить второй прод-шлюз к моделям в обход LiteLLM.
  - n8n при появлении на целевой схеме — дополнение диаграммы, не пересмотр LiteLLM/RAG/IAM.

- **Ссылки:**
  - Схема: [`artifacts/architecture/architecture-in-drawio.drawio`](../architecture/architecture-in-drawio.drawio)
  - Видение и стек: [`CONCEPT.md`](../../CONCEPT.md)
  - Статус этапов: [`ROADMAP.md`](../../ROADMAP.md)
  - Правила агентов: [`AGENTS.md`](../../AGENTS.md)
  - Связанные ADR: [0001](0001-architecture-as-code.md), [0002](0002-github-monorepo.md), [0004](0004-postgresql-native-local.md)–[0009](0009-metabase-native-local.md), [0007](0007-edge-nginx-npm.md), [0010](0010-games-static-app.md), [0011](0011-ai-gateway-litellm.md), [0012](0012-agent1-langgraph-stack.md), [0013](0013-agent2-crewai.md), [0014](0014-agent3-autogen-n8n-dify.md), [0019](0019-cabinet-ssr-bff-authentik.md) (кабинет, SSR/BFF, проверка JWT — уточняет Frontend и роль Nginx)
  - БК1: [`artifacts/business-cases/bc1/`](../business-cases/bc1/)

workspace "alexsoft" "Personal Ecosystem Lab — целевая архитектура (C4 L1–L3)" {

    !identifiers hierarchical

    model {
        user = person "Пользователь" "Лендинг (без входа); после логина — личный кабинет: список агентов, Q&A по проекту (БК1)."
        admin = person "Администратор" "Владелец платформы: админ-панель в кабинете, разработка, деплой, эксплуатация, BI и метрики."

        llmProviders = softwareSystem "ИИ модели" "Облачные модели DeepSeek, Qwen, ChatGPT, Claude, Gemini." "External"
        embeddingModel = softwareSystem "Embedding" "text-embedding-3-small (облачная); вызывается только через AI Gateway." "External"
        cursor = softwareSystem "Cursor" "IDE на ноутбуке: изменение кода целевой платформы." "External"
        github = softwareSystem "GitHub" "Монорепозиторий и GitHub Actions (CI/CD); секреты CI в GitHub Secrets, не в git." "External"

        alexsoft = softwareSystem "alexsoft" "Персональная мультисервисная платформа на VPS/VDS: edge, приложения, данные, ИИ-контур, observability, BI. Секреты хранятся вне git (.env / GitHub Secrets)." {

            edge = container "Edge" "API Gateway / веб-сервер: TLS, раздача статики лендинга и игр, reverse proxy на кабинет (/app, /api) и на страницу входа IAM. JWT сам не проверяет (ADR-0019)." "Nginx" {
                reverseProxy = component "Reverse proxy / TLS" "Терминация HTTPS, маршруты /app, /api к кабинету, вход к IAM." "Nginx"
                staticServe = component "Раздача статики" "Отдача готовых файлов лендинга, портфолио и игр с диска." "Nginx"
            }

            iam = container "IAM" "Аутентификация и авторизация (OIDC): вход, группы user / admin, выдача JWT." "Authentik"

            landing = container "Frontend лендинга и игр" "Лендинг, портфолио, игры. Статика (SSG), без входа и без серверного процесса: раздаёт Edge." "Next.js (output: export)"

            cabinet = container "Frontend кабинета" "Личный кабинет и админ-панель: вход через IAM, список агентов, чат, управление. SSR (Node) и BFF: токены остаются на сервере, в браузер идёт cookie сессии." "Next.js (SSR)"

            businessLogic = container "Business Logic" "REST API для кабинета: проверка JWT (JWKS IAM) и ролей user / admin, список агентов, запуск Q&A, статус (SSE); публикация запусков в RabbitMQ; БД, файлы, кэш." "FastAPI (Python)" {
                authz = component "JWT и роли" "Проверка подписи JWT по JWKS IAM, claims, роли user / admin и ACL на агента или коллекцию." "FastAPI"
                apiOrchestration = component "API" "REST API: список агентов, запуск Q&A, статус (SSE)." "FastAPI"
                agentRegistry = component "Реестр агентов и адаптеры" "Реестр агентов (bl.agents), запуски и события (bl.runs), адаптеры echo / LangGraph Agent Server; суточная квота запусков на пользователя." "FastAPI"
                workersBridge = component "Async bridge" "Публикация запуска агента в брокер (publish); кэш get/set." "FastAPI"
            }

            agentPlatform = container "Agent Platform" "Платформы агентов: код и UI без кода." "LangGraph + LangSmith Studio + LangFlow; Dify" {
                codeAgents = component "Code agents" "Серьёзные агенты кодом: граф состояний, IDE, drag-and-drop." "LangGraph + LangSmith Studio + LangFlow"
                uiAgents = component "UI agents" "Агенты через UI без кода." "Dify"
            }

            rag = container "RAG" "Слой загрузки, очистки, чанкинга и retrieval по корпусу проекта." "LlamaIndex" {
                ingest = component "Load / clean / chunk" "Загрузка документов, очистка, чанкинг." "LlamaIndex"
                embedClient = component "Embedding client" "Query и index embeddings через AI Gateway (text-embedding-3-small)." "LlamaIndex → LiteLLM"
                retrieve = component "Hybrid retrieve" "Hybrid search / upsert в векторной БД." "LlamaIndex + Qdrant"
            }

            guardrails = container "Guardrails" "Синхронные pre/post проверки вокруг вызовов моделей." "LLM Guard"

            aiGateway = container "AI Gateway" "Единый OpenAI-compatible шлюз к облачным LLM и embeddings; единственный путь к провайдерам." "LiteLLM"

            postgres = container "PostgreSQL" "Реляционное хранилище приложения и метаданных." "PostgreSQL"
            minio = container "MinIO" "Объектное хранилище документов корпуса." "MinIO"
            qdrant = container "Qdrant" "Векторная БД; hybrid retrieval." "Qdrant"
            redis = container "Redis" "Кэш (в т.ч. ответов AI)." "Redis"
            rabbitmq = container "RabbitMQ" "Брокер сообщений: запуски агентов (publish от BL, consume run на Agent Platform) — целевой, этап 6; на этапе 5 BL вызывает Agent Platform напрямую." "RabbitMQ"

            observability = container "Observability" "Логи, метрики инфры и аналитика LLM-прогонов (как на draw.io: Loki/Alloy/Prometheus/Grafana + LangSmith)." "Grafana + Loki + Prometheus + Alloy; LangSmith" {
                alloy = component "Log/metrics agent" "Сбор логов и метрик с хоста/сервисов." "Grafana Alloy"
                loki = component "Log store" "Хранилище логов." "Loki"
                prometheus = component "Metrics store" "Сбор и хранение метрик." "Prometheus"
                grafana = component "Dashboards" "Анализ метрик и логов." "Grafana"
                langSmith = component "LLM traces / evals" "Хранение и мониторинг LLM-прогонов (не путать с LangSmith Studio в Agent Platform)." "LangSmith"
            }

            metabase = container "Metabase" "BI-дашборды поверх PostgreSQL." "Metabase"
        }

        # --- L1 ---
        user -> alexsoft "HTTPS: лендинг, логин, кабинет, агенты, Q&A"
        admin -> alexsoft "HTTPS: админ-панель; эксплуатация, BI, деплой через delivery"
        admin -> cursor "Разрабатывает"
        cursor -> github "Пуш кода"
        github -> alexsoft "GitHub Actions деплоит на VDS/VPS"
        alexsoft -> llmProviders "Вызовы LLM (только через AI Gateway)"
        alexsoft -> embeddingModel "Embeddings (только через AI Gateway)"

        # --- L2: perimeter & apps ---
        user -> alexsoft.edge "HTTPS"
        admin -> alexsoft.edge "HTTPS"
        alexsoft.edge -> alexsoft.landing "раздача файлов"
        alexsoft.edge -> alexsoft.iam "reverse proxy: вход / OIDC"
        alexsoft.edge -> alexsoft.cabinet "reverse proxy /app (+ /app/api)"
        alexsoft.cabinet -> alexsoft.iam "OIDC (обмен кода)"
        alexsoft.cabinet -> alexsoft.businessLogic "HTTPS REST (+ SSE статуса), JWT"
        alexsoft.businessLogic -> alexsoft.iam "JWKS (проверка JWT)"

        # --- L2: BL ---
        alexsoft.businessLogic -> alexsoft.postgres "SQL"
        alexsoft.businessLogic -> alexsoft.minio "Файлы / артефакты"
        alexsoft.businessLogic -> alexsoft.redis "cache get/set"
        alexsoft.businessLogic -> alexsoft.rabbitmq "publish (целевой, этап 6)"
        alexsoft.businessLogic -> alexsoft.agentPlatform "HTTPS run (этап 5, без брокера)"
        alexsoft.businessLogic -> alexsoft.aiGateway "HTTPS"

        # --- L2: AI contour ---
        alexsoft.rabbitmq -> alexsoft.agentPlatform "consume run (целевой, этап 6)"
        alexsoft.agentPlatform -> alexsoft.rag "HTTPS search/retrieve"
        alexsoft.agentPlatform -> alexsoft.guardrails "sync pre/post check"
        alexsoft.agentPlatform -> alexsoft.aiGateway "OpenAI-compatible HTTPS"
        alexsoft.rag -> alexsoft.guardrails "sync"
        alexsoft.rag -> alexsoft.aiGateway "embeddings + LLM"
        alexsoft.guardrails -> alexsoft.aiGateway "OpenAI-compatible HTTPS"
        alexsoft.aiGateway -> llmProviders "HTTPS + ключ провайдера"
        alexsoft.aiGateway -> embeddingModel "HTTPS + ключ провайдера"
        alexsoft.aiGateway -> alexsoft.observability "LiteLLM пишет трейс (LangSmith)"
        alexsoft.agentPlatform -> alexsoft.observability "граф, инструменты, ошибки шагов (LangSmith)"
        alexsoft.aiGateway -> alexsoft.redis "LLM response cache (sync)"

        alexsoft.rag -> alexsoft.minio "read documents"
        alexsoft.rag -> alexsoft.qdrant "upsert / search"

        # --- L2: BI & observability ---
        alexsoft.metabase -> alexsoft.postgres "read-only SQL"
        admin -> alexsoft.metabase "Дашборды BI"
        admin -> alexsoft.observability "Дашборды и алерты"
        alexsoft.edge -> alexsoft.observability "Метрики и логи"
        alexsoft.cabinet -> alexsoft.observability "Метрики и логи"
        alexsoft.businessLogic -> alexsoft.observability "Метрики и логи"
        alexsoft.agentPlatform -> alexsoft.observability "Метрики и логи"
        alexsoft.rag -> alexsoft.observability "Метрики и логи"
        alexsoft.aiGateway -> alexsoft.observability "Метрики и логи"
        alexsoft.postgres -> alexsoft.observability "Метрики и логи"
        alexsoft.minio -> alexsoft.observability "Метрики и логи"
        alexsoft.qdrant -> alexsoft.observability "Метрики и логи"
        alexsoft.redis -> alexsoft.observability "Метрики и логи"
        alexsoft.rabbitmq -> alexsoft.observability "Метрики и логи"

        # --- L3 relationships ---
        alexsoft.edge.staticServe -> alexsoft.landing "раздача файлов"
        alexsoft.edge.reverseProxy -> alexsoft.cabinet "reverse proxy /app (+ /app/api)"
        alexsoft.edge.reverseProxy -> alexsoft.iam "reverse proxy: вход / OIDC"

        alexsoft.businessLogic.authz -> alexsoft.iam "JWKS (проверка JWT)"
        alexsoft.businessLogic.apiOrchestration -> alexsoft.postgres "SQL"
        alexsoft.businessLogic.apiOrchestration -> alexsoft.minio "Файлы / артефакты"
        alexsoft.businessLogic.apiOrchestration -> alexsoft.businessLogic.agentRegistry "запуск агента, квота"
        alexsoft.businessLogic.agentRegistry -> alexsoft.postgres "SQL (схема bl)"
        alexsoft.businessLogic.agentRegistry -> alexsoft.agentPlatform "HTTPS run (этап 5, без брокера)"
        alexsoft.businessLogic.workersBridge -> alexsoft.rabbitmq "publish"
        alexsoft.businessLogic.workersBridge -> alexsoft.redis "cache get/set"

        alexsoft.agentPlatform.codeAgents -> alexsoft.rag "retrieve"
        alexsoft.agentPlatform.uiAgents -> alexsoft.rag "retrieve"
        alexsoft.agentPlatform.codeAgents -> alexsoft.guardrails "pre/post"
        alexsoft.agentPlatform.uiAgents -> alexsoft.guardrails "pre/post"

        alexsoft.rag.ingest -> alexsoft.minio "read documents"
        alexsoft.rag.embedClient -> alexsoft.aiGateway "embeddings + LLM"
        alexsoft.rag.retrieve -> alexsoft.qdrant "hybrid upsert / search"

        alexsoft.observability.alloy -> alexsoft.observability.loki "Пишет логи"
        alexsoft.observability.alloy -> alexsoft.observability.prometheus "Скрейп / remote write"
        alexsoft.observability.grafana -> alexsoft.observability.loki "Запросы логов"
        alexsoft.observability.grafana -> alexsoft.observability.prometheus "Запросы метрик"
        alexsoft.aiGateway -> alexsoft.observability.langSmith "LiteLLM пишет трейс"
        alexsoft.agentPlatform -> alexsoft.observability.langSmith "Трейсы агентных прогонов"
    }

    views {
        systemLandscape "SystemLandscape" {
            include *
            autoLayout lr
            description "C4 — landscape целевой экосистемы alexsoft (draw.io / ADR-0015)."
        }

        systemContext alexsoft "SystemContext" {
            include *
            autoLayout lr
            description "C4 Level 1 — системный контекст целевой архитектуры."
        }

        container alexsoft "Containers" {
            include *
            autoLayout tb
            description "C4 Level 2 — контейнеры целевой архитектуры (architecture-in-drawio)."
        }

        component alexsoft.edge "ComponentsEdge" {
            include *
            autoLayout tb
            description "C4 Level 3 — Edge (Nginx): статика и reverse proxy, без проверки JWT."
        }

        component alexsoft.businessLogic "ComponentsBusinessLogic" {
            include *
            autoLayout tb
            description "C4 Level 3 — Business Logic (FastAPI): JWT и роли, API, async bridge."
        }

        component alexsoft.agentPlatform "ComponentsAgentPlatform" {
            include *
            autoLayout tb
            description "C4 Level 3 — Agent Platform (LangGraph stack + Dify)."
        }

        component alexsoft.rag "ComponentsRAG" {
            include *
            autoLayout tb
            description "C4 Level 3 — RAG (LlamaIndex)."
        }

        component alexsoft.observability "ComponentsObservability" {
            include *
            autoLayout tb
            description "C4 Level 3 — Observability (Alloy, Loki, Prometheus, Grafana)."
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }
}

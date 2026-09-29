workspace "alexsoft" "Personal Ecosystem Lab — персональная мультисервисная платформа" {

    !identifiers hierarchical

    model {
        visitor = person "Посетитель" "Смотрит визитку, портфолио и живые демо продуктов."
        operator = person "Оператор" "Владелец платформы: разрабатывает, деплоит, смотрит метрики и BI."

        llm = softwareSystem "LLM API" "Внешние модели (Qwen / DeepSeek / ChatGPT и др.)." "External"
        messengers = softwareSystem "Мессенджеры и почта" "Каналы доставки ответов и постов." "External"
        github = softwareSystem "GitHub" "Монорепозиторий, Actions, артефакты." "External"

        alexsoft = softwareSystem "alexsoft" "Персональная платформа: лендинг, продукты, данные, AI-агенты, DevOps-контур." {

            landing = container "Landing" "Визитка, портфолио, кнопки перехода к демо." "Next.js"
            games = container "Games" "Мини-игры: каталог /games (Контур, Вайб-чек, Десант). Отдельное Next.js-приложение; статика склеивается с лендингом в CI." "Next.js"
            rag = container "RAG" "Поиск и ответы по собственной базе знаний." "TBD"
            agent1 = container "Agent 1" "Оркестрация агента на LangGraph; IDE — LangSmith Studio; визуальный билдер — LangFlow." "LangGraph"
            agent2 = container "Agent 2" "Multi-agent crew на CrewAI (роли/задачи); продукт — черновик поста. CLI, без локального Studio." "CrewAI"
            agent3 = container "Agent 3" "Multi-agent conversation на AutoGen AgentChat; CLI smoke; продукт — после стека 5.4." "AutoGen"
            n8n = container "n8n" "Low-code оркестрация workflow; LLM только через AI Gateway." "n8n"
            dify = container "Dify" "Low-code AI platform (Docker Compose на ноутбуке); LLM только через AI Gateway." "Dify"
            aiGateway = container "AI Gateway" "Единый шлюз к облачным LLM (OpenAI-compatible); агенты и RAG ходят только через него." "LiteLLM"
            dataPlatform = container "Data Platform" "PostgreSQL, Redis, MinIO, ETL; витрины для BI." "PostgreSQL, Redis, MinIO"
            observability = container "Observability" "Логи, метрики, дашборды." "Grafana, Loki, Prometheus"
        }

        visitor -> alexsoft "Открывает лендинг, запускает демо"
        operator -> alexsoft "Разрабатывает, эксплуатирует, анализирует"
        operator -> github "Пушит код, смотрит CI"
        alexsoft -> llm "Запросы агентов и RAG"
        alexsoft -> messengers "Публикация постов и ответов"
        alexsoft -> github "CI экспортирует архитектурные артефакты"

        # L2 (контейнеры) — связи для следующих уровней; на L1 не показываются
        visitor -> alexsoft.landing "HTTPS"
        alexsoft.landing -> alexsoft.games "Переход к демо"
        alexsoft.landing -> alexsoft.rag "Переход к демо"
        alexsoft.landing -> alexsoft.aiGateway "Переход к демо"
        alexsoft.landing -> alexsoft.agent1 "Переход к демо"
        alexsoft.landing -> alexsoft.agent2 "Переход к демо"
        alexsoft.games -> alexsoft.dataPlatform "Состояние партий / профили"
        alexsoft.rag -> alexsoft.dataPlatform "Документы и индексы"
        alexsoft.agent1 -> alexsoft.aiGateway "LLM через шлюз"
        alexsoft.agent1 -> alexsoft.dataPlatform "Состояние / артефакты запусков"
        alexsoft.agent2 -> alexsoft.aiGateway "LLM через шлюз"
        alexsoft.agent2 -> alexsoft.dataPlatform "Состояние / артефакты запусков"
        alexsoft.agent3 -> alexsoft.aiGateway "LLM через шлюз"
        alexsoft.agent3 -> alexsoft.dataPlatform "Состояние / артефакты запусков"
        alexsoft.n8n -> alexsoft.aiGateway "LLM через шлюз"
        alexsoft.dify -> alexsoft.aiGateway "LLM через шлюз"
        alexsoft.aiGateway -> alexsoft.dataPlatform "Контекст, артефакты, логи запусков"
        alexsoft.aiGateway -> llm "Вызовы моделей"
        alexsoft.aiGateway -> messengers "Доставка сообщений"
        operator -> alexsoft.observability "Дашборды и алерты"
        alexsoft.landing -> alexsoft.observability "Метрики и логи"
        alexsoft.games -> alexsoft.observability "Метрики и логи"
        alexsoft.rag -> alexsoft.observability "Метрики и логи"
        alexsoft.agent1 -> alexsoft.observability "Метрики и логи"
        alexsoft.agent2 -> alexsoft.observability "Метрики и логи"
        alexsoft.agent3 -> alexsoft.observability "Метрики и логи"
        alexsoft.n8n -> alexsoft.observability "Метрики и логи"
        alexsoft.dify -> alexsoft.observability "Метрики и логи"
        alexsoft.aiGateway -> alexsoft.observability "Метрики и логи"
        alexsoft.dataPlatform -> alexsoft.observability "Метрики и логи"
    }

    views {
        systemLandscape "SystemLandscape" {
            include *
            autoLayout lr
            description "Контекст экосистемы alexsoft и внешние системы."
        }

        systemContext alexsoft "SystemContext" {
            include *
            autoLayout lr
            description "C4 Level 1 — системный контекст Personal Ecosystem Lab."
        }

        container alexsoft "Containers" {
            include *
            autoLayout tb
            description "C4 Level 2 — контейнеры (черновик; детализация на следующих этапах)."
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
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }
}

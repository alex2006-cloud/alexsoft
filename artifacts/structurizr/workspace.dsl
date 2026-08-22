workspace "alexsoft" "Personal Ecosystem Lab — персональная мультисервисная платформа" {

    !identifiers hierarchical

    model {
        visitor = person "Посетитель" "Смотрит визитку, портфолио и живые демо продуктов."
        operator = person "Оператор" "Владелец платформы: разрабатывает, деплоит, смотрит метрики и BI."

        llm = softwareSystem "LLM API" "Внешние модели (OpenAI / Anthropic и др.)." "External"
        messengers = softwareSystem "Мессенджеры и почта" "Каналы доставки ответов и постов." "External"
        github = softwareSystem "GitHub" "Монорепозиторий, Actions, артефакты." "External"

        alexsoft = softwareSystem "alexsoft" "Персональная платформа: лендинг, продукты, данные, AI-агенты, DevOps-контур." {

            landing = container "Landing" "Визитка, портфолио, кнопки перехода к демо." "Next.js"
            games = container "Games" "Мини-игры как отдельные продукты." "TBD"
            rag = container "RAG" "Поиск и ответы по собственной базе знаний." "TBD"
            aiGateway = container "AI Gateway" "Единый шлюз/оркестратор агентов: посты, тестировщик, ответы в каналы." "LangChain/LangGraph"
            dataPlatform = container "Data Platform" "PostgreSQL, MinIO, ETL; витрины для BI." "PostgreSQL, MinIO"
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
        alexsoft.games -> alexsoft.dataPlatform "Состояние партий / профили"
        alexsoft.rag -> alexsoft.dataPlatform "Документы и индексы"
        alexsoft.aiGateway -> alexsoft.dataPlatform "Контекст, артефакты, логи запусков"
        alexsoft.aiGateway -> llm "Вызовы моделей"
        alexsoft.aiGateway -> messengers "Доставка сообщений"
        operator -> alexsoft.observability "Дашборды и алерты"
        alexsoft.landing -> alexsoft.observability "Метрики и логи"
        alexsoft.games -> alexsoft.observability "Метрики и логи"
        alexsoft.rag -> alexsoft.observability "Метрики и логи"
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

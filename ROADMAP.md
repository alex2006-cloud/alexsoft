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

По [CONCEPT.md](CONCEPT.md). **Redis-кеш ответов и RabbitMQ — после ИИ-блока**, не блокируют первые AI-продукты (Memurai уже стоит с этапа 2, но в AI пока не встраиваем).  
**AI Gateway = LiteLLM** (не путать с API Gateway / IAM — этап 6). Облачные LLM: Qwen, DeepSeek, ChatGPT. Три агента подряд, у каждого свой продукт; затем RAG-продукт.  
**LangSmith Studio** (IDE графа; бывш. LangGraph Studio) ≠ **LangSmith** (платформа трейсов/evals).

**5.1 — AI Gateway + первая LLM**

- [ ] LiteLLM (локально)
- [ ] Подключить **Qwen** (далее DeepSeek / ChatGPT по мере надобности)
- [ ] Ключи в `.env`, проверка одного запроса через шлюз
- [ ] ADR: AI Gateway = LiteLLM

**5.2 — агент 1 (LangGraph) + продукт**

- [ ] LangChain / LangGraph + LangSmith Studio (IDE; бывш. LangGraph Studio) + LangFlow (через LiteLLM)
- [ ] AI-продукт через агент 1 (пост / тестировщик / ответы в каналы — один сценарий)
- [ ] Демо / ссылка с лендинга (Lab), когда готово
- [ ] ADR: агент 1 = LangGraph-стек

**5.3 — агент 2 (CrewAI) + продукт**

- [ ] CrewAI через LiteLLM
- [ ] AI-продукт через агент 2
- [ ] ADR: CrewAI vs LangGraph

**5.4 — агент 3 (AutoGen) + продукт**

- [ ] AutoGen через LiteLLM
- [ ] AI-продукт через агент 3
- [ ] ADR: AutoGen vs LangGraph / CrewAI

**5.5 — векторная БД + RAG + продукт с RAG**

- [ ] Выбор ВБД: Qdrant **или** Weaviate (ADR)
- [ ] RAG, 3 слоя: загрузка → хранение эмбеддингов → пайплайны поиска (LangChain / LlamaIndex — ADR)
- [ ] `apps/rag` + AI-продукт **с RAG**
- [ ] Lab «RAG» → Live (когда есть URL)

**5.6 — LangSmith (платформа, не Studio)**

- [ ] Довести LangSmith (платформа): трейсы, анализ, оценка прогонов — не путать с LangSmith Studio
- [ ] Зафиксировать: Loki/Grafana ≠ LangSmith (платформа) ≠ LangSmith Studio (IDE)

**5.7 — после ИИ-блока (не критично сейчас)**

- [ ] Интеграция Redis/Memurai — кеш ответов AI
- [ ] RabbitMQ — очередь долгих AI-задач
- [ ] ADR + порты в `.env` / README

## Этап 6 — облако и комплаенс

Сначала обсуждение «что переносим». Затем по CONCEPT:

- [ ] Архитектура переноса (Structurizr / ADR)
- [ ] API Gateway (инструмент — уточнить)
- [ ] IAM (инструмент — уточнить)
- [ ] SSH, Docker на VDS (+ опционально Portainer)
- [ ] Redis вместо Memurai; Postgres/MinIO в облаке; туннели к DBeaver / Console
- [ ] Observability и Metabase на VDS (по необходимости)
- [ ] k3s
- [ ] Kafka (если понадобится сверх RabbitMQ)
- [ ] Заявка в РКН как оператор ПДн — только если появятся ПДн субъектов РФ в проде

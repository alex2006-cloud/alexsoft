# RAG

Сервис поиска и ответов по собственной базе знаний: **LlamaIndex** (load / clean / chunk) + hybrid-поиск в **Qdrant** (dense + BM25, fusion RRF/DBSF). Embedding `text-embedding-3-small` и LLM — только через **LiteLLM** ([ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md), реализация — [ADR-0017](../../artifacts/adr/0017-rag-service-implementation.md)).

**Статус (этап 5.6):** сервис реализован и покрыт тестами (unit, интеграционные на реальных Qdrant/Postgres/MinIO с fake-embeddings, контрактные). Живой прогон на `text-embedding-3-small` требует `OPENAI_API_KEY` в `.env` — см. «Первый запуск».

## API-контракт

[`artifacts/api/rag.openapi.yaml`](../../artifacts/api/rag.openapi.yaml) (OpenAPI 3.1, contract-first). Сначала меняем контракт, потом код; `tests/test_contract.py` падает, если реализация расходится с контрактом (операции, `operationId`, свойства схем, лишние эндпоинты).

| Слой | Эндпоинты |
|---|---|
| Загрузка | `POST /v1/collections/{c}/documents` (202 + Job), `GET /v1/jobs/{id}` |
| Хранение | `/v1/collections`, `/v1/collections/{c}/documents[/{id}]` |
| Поиск | `POST /v1/search` (hybrid), `POST /v1/query` (ответ с цитатами) |
| Служебные | `GET /health/live`, `GET /health/ready` (postgres, qdrant, minio, litellm) |

Swagger UI сервиса: http://127.0.0.1:8200/docs. Проверка контракта: `npx @redocly/cli lint artifacts/api/rag.openapi.yaml` (или `docker run ... redocly/cli lint`).

## Как устроено

```
inline | MinIO ─► Loader ─► Parse&Clean ─► Chunking (LlamaIndex) ─► Embed ─► Qdrant upsert     (ingest, фоновая задача + Job)
                                               dense: LiteLLM text-embedding-3-small
                                               sparse: fastembed Qdrant/bm25 (локально)
query ─► embed(dense+sparse) ─► Qdrant query_points(prefetch dense & sparse, RRF|DBSF, filter) ─► чанки
       └► /v1/query: Guard(pre) ─► контекст ─► LiteLLM LLM ─► Guard(post) ─► ответ + citations
```

- **Коллекция** = коллекция Qdrant с векторами `dense` (1536, cosine) и `sparse` (BM25, IDF). Модель embedding фиксируется на коллекции при создании; смена модели = новая коллекция.
- **Состояние** (коллекции, документы, Job, Idempotency-Key) — PostgreSQL, схема `rag` в БД `alexsoft` (DDL создаётся при старте).
- **Идемпотентность:** повторный `POST` с тем же `external_id` обновляет чанки на месте (точки с детерминированными id, хвост удаляется, поиск не «проваливается»); `Idempotency-Key` возвращает исходный Job.
- **Чанкинг:** `markdown` (по заголовкам + деление больших секций + склейка крошечных), `sentence`, `token`; параметры по коллекции или документу (`ChunkingConfig`). В текст для embedding добавляется путь заголовков.
- **Score:** `score` в ответе нормирован в [0, 1] (RRF: 1.0 = первое место и в dense, и в sparse; DBSF: доля максимума), `score_threshold` действует на него.
- **Источники:** UTF-8 текст/markdown (inline или объект MinIO). PDF/Office — позже (отдельный парсер).
- **Auth этапа 5:** заголовок `X-API-Key` = `RAG_API_KEY`; пустой ключ = все защищённые методы отвечают 401 (fail closed). JWT Authentik — этап 6.
- **LLM Guard:** интерфейс `GuardrailsClient`; сейчас `NoopGuard` (`LLM_GUARD_ENABLED=false`). Реальный Guard — этап 6.
- **Ошибки:** `application/problem+json` (RFC 9457) с `code`; `X-Request-Id` принимается и возвращается.
- **Не включено в 5.6:** LangSmith-трейсы (`trace_id` в ответе пока не заполняется), rerank, Redis-кеш, RabbitMQ.

## Первый запуск (Windows, нативно)

Нужны: PostgreSQL, MinIO, LiteLLM (с `OPENAI_API_KEY` для embeddings и `DEEPSEEK_API_KEY` для ответов).

```powershell
# 1. зависимости инфраструктуры
powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1
powershell -ExecutionPolicy Bypass -File infra\qdrant\start-qdrant.ps1
powershell -ExecutionPolicy Bypass -File infra\minio\start-minio.ps1
powershell -ExecutionPolicy Bypass -File infra\litellm\start-litellm.ps1      # после добавления OPENAI_API_KEY в .env
powershell -ExecutionPolicy Bypass -File infra\litellm\smoke-embeddings.ps1

# 2. сервис RAG (venv: %LOCALAPPDATA%\AlexsoftRag\venv)
powershell -ExecutionPolicy Bypass -File infra\rag\install-rag.ps1
powershell -ExecutionPolicy Bypass -File infra\rag\start-rag.ps1               # http://127.0.0.1:8200
powershell -ExecutionPolicy Bypass -File infra\rag\smoke-rag.ps1               # коллекция -> ingest -> search -> query

# 3. корпус проекта (ADR, CONCEPT, ROADMAP, README, БК1) и оценка качества
powershell -ExecutionPolicy Bypass -File infra\rag\seed-corpus.ps1
& "$env:LOCALAPPDATA\AlexsoftRag\venv\Scripts\python.exe" apps\rag\eval\run_eval.py --answer

powershell -ExecutionPolicy Bypass -File infra\rag\stop-rag.ps1
```

Пример:

```powershell
curl.exe -s -X POST http://127.0.0.1:8200/v1/search -H "X-API-Key: <key>" -H "Content-Type: application/json" `
  -d '{"collection":"project-docs","query":"Зачем RabbitMQ на этапе 6?","top_k":5}'
```

Переменные `.env`: `RAG_*`, `QDRANT_*`, `LLM_GUARD_ENABLED` — см. `.env.example`. Первый старт скачивает BM25-модель с Hugging Face (интернет нужен один раз).

> Windows с системным прокси (Clash/V2Ray): клиент Qdrant и LiteLLM-клиент работают с `trust_env=False`, локальные вызовы идут мимо прокси.

## Тесты

```powershell
cd apps\rag
& "$env:LOCALAPPDATA\AlexsoftRag\venv\Scripts\python.exe" -m pytest -q
```

| Файл | Что проверяет | Требует |
|---|---|---|
| `tests/test_units.py` | чанкинг, очистка, фильтры, нормализация score, цитаты, guard | ничего |
| `tests/test_contract.py` | паритет с `rag.openapi.yaml` | ничего |
| `tests/test_integration.py` | CRUD, ingest → search → query, фильтры, идемпотентность, MinIO, ошибки | Postgres, Qdrant, MinIO (иначе skip) |
| `tests/test_corpus.py` | реальный корпус проекта: hit@5 ≥ 0.7 на гибридном пути (dense — hashing stand-in) | Postgres, Qdrant, MinIO (иначе skip) |

Оценка на живых embeddings — `eval/run_eval.py` (набор `eval/questions.yaml`: hit@k, MRR, проверка `insufficient_context` на вопросе вне корпуса).

## Структура

`alexsoft_rag/` — `api/` (роутеры по тегам контракта), `ingest/` (loader, parser, chunker, pipeline), `store/` (postgres, qdrant), `retrieval/` (sparse, search, query), `clients/` (litellm, minio, guard), `schemas.py`, `config.py`, `errors.py`, `main.py`.

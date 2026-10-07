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
inline | MinIO ─► Loader ─► Parser (по формату) ─► Segments+locator ─► Chunking ─► Embed ─► Qdrant upsert   (ingest, фоновая задача + Job)
                  md/txt | код | PDF (+vision OCR) | Excel | bpmn/drawio
                                               dense: LiteLLM text-embedding-3-small
                                               sparse: fastembed Qdrant/bm25 (локально)
query ─► embed(dense+sparse) ─► Qdrant query_points(prefetch dense & sparse, RRF|DBSF, filter) ─► чанки
       └► /v1/query: Guard(pre) ─► контекст ─► LiteLLM LLM ─► Guard(post) ─► ответ + citations
```

- **Коллекция** = коллекция Qdrant с векторами `dense` (1536, cosine) и `sparse` (BM25, IDF). Модель embedding фиксируется на коллекции при создании; смена модели = новая коллекция.
- **Состояние** (коллекции, документы, Job, Idempotency-Key) — PostgreSQL, схема `rag` в БД `alexsoft` (DDL создаётся при старте).
- **Идемпотентность:** повторный `POST` с тем же `external_id` обновляет чанки на месте (точки с детерминированными id, хвост удаляется, поиск не «проваливается»); `Idempotency-Key` возвращает исходный Job.
- **Чанкинг:** `auto` (по умолчанию: стратегия по типу содержимого) | `markdown` | `sentence` | `token` | `code` | `pages` | `table`; параметры по коллекции или документу (`ChunkingConfig`). Несовместимая стратегия коллекции не ломает другие форматы (код в «markdown»-коллекции остаётся кодом). В текст для embedding добавляется заголовок (путь заголовков, `File/Language/Symbol`, `файл, стр. N`).
- **Score:** `score` в ответе нормирован в [0, 1] (RRF: 1.0 = первое место и в dense, и в sparse; DBSF: доля максимума), `score_threshold` действует на него.
- **Источники и форматы** ([ADR-0018](../../artifacts/adr/0018-rag-multiformat-ingest-and-project-kb.md)): текст/markdown; **код** (`.py` через `ast`, `.ts/.tsx/.js` по объявлениям, `.ps1/.sql/.yaml/.toml/.conf/.dsl/.puml` блоками; символ и номера строк в `locator`); **PDF** (`pypdf`; страницы без текстового слоя → картинка → vision-модель через LiteLLM, кеш в `rag.page_ocr_cache`); **Excel `.xlsx`** (листы → markdown-таблицы / записи `колонка: значение`, отдельные чанки формул; скрытые листы пропускаются); **`.bpmn`, `.drawio`** (узлы и связи). Inline-источник — только текст. Не поддержано (422): `.docx/.pptx/.xls`, картинки, архивы.
- **Локатор:** каждый `Chunk`/`Citation` несёт `locator` (`path`, `page`, `sheet`+`range`, `line_start/line_end`+`symbol`, `section`) — по нему агент указывает точное место источника.
- **`content_hash`:** если документ с тем же `external_id` уже проиндексирован с таким же хешем, метаданными и чанкингом, ingest возвращает готовый Job и ничего не пересчитывает (экономия токенов embedding).
- **BM25:** язык на коллекцию (`sparse_language`: `russian` для документов, `english` для кода); идентификаторы `snake_case`/`camelCase` разворачиваются в слова.
- **Auth этапа 5:** заголовок `X-API-Key` = `RAG_API_KEY`; пустой ключ = все защищённые методы отвечают 401 (fail closed). JWT Authentik — по архитектуре (локально), не ждать VPS.
- **LLM Guard:** интерфейс `GuardrailsClient`; сейчас `NoopGuard` (`LLM_GUARD_ENABLED=false`). Реальный Guard — целевой контур (после планирования этапа 6).
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

# 3. база знаний о проекте и оценка качества
powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -DryRun        # что будет загружено (без сети)
powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1                # docs + код + PDF/Excel + саммари кода
& "$env:LOCALAPPDATA\AlexsoftRag\venv\Scripts\python.exe" apps\rag\eval\run_eval.py --answer
# минимальный вариант только с документацией (без кода): infra\rag\seed-corpus.ps1

powershell -ExecutionPolicy Bypass -File infra\rag\stop-rag.ps1
```

Пример:

```powershell
curl.exe -s -X POST http://127.0.0.1:8200/v1/search -H "X-API-Key: <key>" -H "Content-Type: application/json" `
  -d '{"collection":"project-docs","query":"Зачем RabbitMQ на этапе 6?","top_k":5}'
```

Переменные `.env`: `RAG_*`, `QDRANT_*`, `LLM_GUARD_ENABLED` — см. `.env.example`. Первый старт скачивает BM25-модель с Hugging Face (интернет нужен один раз).

> Windows с системным прокси (Clash/V2Ray): клиент Qdrant и LiteLLM-клиент работают с `trust_env=False`, локальные вызовы идут мимо прокси.

## База знаний о проекте (`kb-sync`)

Две коллекции ([ADR-0018](../../artifacts/adr/0018-rag-multiformat-ingest-and-project-kb.md)): **`project-docs`** (ADR, CONCEPT/ROADMAP, README, архитектура `.dsl/.puml/.drawio/.bpmn`, OpenAPI, PDF, Excel; BM25 `russian`) и **`project-code`** (`apps/`, `infra/`, скрипты, конфиги + краткие LLM-описания файлов `summary/<path>.md`; BM25 `english`). Что и куда попадает — `kb/sources.yaml`.

`kb-sync.ps1` берёт файлы из `git ls-files` (+ новые неигнорируемые), считает sha256 и грузит только изменённое (MinIO → ingest с `content_hash`), удаляет из индекса документы исчезнувших файлов и **не индексирует секреты**: `.env*` (кроме `.env.example`), `*.pem/*.key`, `credentials.json` — по имени, остальное — сканером токенов/паролей; подозрительные файлы попадают в отчёт, а не в индекс. Саммари кода генерирует `deepseek` через LiteLLM и кеширует на диске по хешу файла (`-NoSummaries` отключает).

```powershell
powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -DryRun -VerboseSkips
powershell -ExecutionPolicy Bypass -File infra\rag\kb-sync.ps1 -Only "apps/rag/**" -Force
```

> Доступ к `project-code` — только по `X-API-Key` на localhost; публично — после IAM / личного кабинета.

## Тесты

```powershell
cd apps\rag
& "$env:LOCALAPPDATA\AlexsoftRag\venv\Scripts\python.exe" -m pytest -q
```

| Файл | Что проверяет | Требует |
|---|---|---|
| `tests/test_units.py` | чанкинг, очистка, фильтры, нормализация score, цитаты, guard | ничего |
| `tests/test_parsers.py` | код (символы, номера строк), Excel (таблицы, формулы), PDF (текст + OCR сканов), bpmn/drawio | ничего |
| `tests/test_kbsync.py` | правила выбора файлов, сканер секретов, инкрементальная синхронизация, формат eval | ничего |
| `tests/test_contract.py` | паритет с `rag.openapi.yaml` | ничего |
| `tests/test_integration.py` | CRUD, ingest → search → query, фильтры, идемпотентность, MinIO, ошибки | Postgres, Qdrant, MinIO (иначе skip) |
| `tests/test_corpus.py` | реальный корпус проекта: hit@5 ≥ 0.7 на гибридном пути (dense — hashing stand-in) | Postgres, Qdrant, MinIO (иначе skip) |

Оценка на живых embeddings — `eval/run_eval.py` (набор `eval/questions.yaml`: hit@k, MRR, проверка `insufficient_context` на вопросе вне корпуса).

## Структура

`alexsoft_rag/` — `api/` (роутеры по тегам контракта), `parsers/` (реестр форматов: text, code, xlsx, pdf, diagrams), `ingest/` (loader, chunker, code_chunker, pipeline), `store/` (postgres, qdrant), `retrieval/` (sparse, search, query), `clients/` (litellm, vision, minio, guard), `kbsync/` (синхронизация репозитория с КБ), `schemas.py`, `config.py`, `errors.py`, `main.py`. `kb/sources.yaml` — источники КБ; `eval/` — вопросы и `run_eval.py`.

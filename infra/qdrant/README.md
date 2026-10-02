# Qdrant (локально, Windows, нативно)

Векторная БД для RAG ([ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md), [ADR-0017](../../artifacts/adr/0017-rag-service-implementation.md)). Hybrid: dense + sparse в одной коллекции.

| Порт | Назначение |
|---|---|
| `6333` | REST + Web UI (`/dashboard`) |
| `6334` | gRPC |

Бинарник и данные вне репозитория: `%LOCALAPPDATA%\Qdrant\` (`qdrant.exe`, `storage\`, `snapshots\`, логи).

## Запуск

```powershell
powershell -ExecutionPolicy Bypass -File infra\qdrant\install-qdrant.ps1
powershell -ExecutionPolicy Bypass -File infra\qdrant\start-qdrant.ps1
# проверка
curl.exe http://127.0.0.1:6333/healthz
# остановка
powershell -ExecutionPolicy Bypass -File infra\qdrant\stop-qdrant.ps1
```

## Переменные `.env`

- `QDRANT_HTTP_PORT` (по умолчанию 6333), `QDRANT_GRPC_PORT` (6334).
- `QDRANT_URL` — адрес для сервисов (`http://127.0.0.1:6333`).
- `QDRANT_API_KEY` — опционально; если задан, Qdrant требует `api-key`, и тот же ключ использует `apps/rag`.

## VPS / облако

Этап 6: Docker Compose (`qdrant/qdrant`), том на диске; наружу не публикуется.

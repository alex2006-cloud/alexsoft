# Loki (локально, Windows)

См. [ADR-0008](../../artifacts/adr/0008-observability-native-local.md). Нативный `loki.exe` — хранилище логов для этапа 3. Своего GUI нет: логи смотрим в Grafana. Docker/Compose — на этапе VPS.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| `loki.exe` | `%LOCALAPPDATA%\Loki\` |
| Данные | `%LOCALAPPDATA%\Loki\data\` |
| Конфиг | `infra/loki/loki-local-config.yaml` |
| Логи процесса | `%LOCALAPPDATA%\Loki\loki.log` |

HTTP API: `http://127.0.0.1:3100` (порт из `.env` → `LOKI_PORT`). gRPC: `9096` (`LOKI_GRPC_PORT`).

## 1. Установка бинарника

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File infra\loki\install-loki.ps1
```

Скрипт качает официальный релиз Loki **v3.7.7** (`loki-windows-amd64.exe.zip`) в `%LOCALAPPDATA%\Loki`. Повторный запуск не перезаписывает уже скачанный `loki.exe`.

## 2. `.env`

```
LOKI_HOST=localhost
LOKI_PORT=3100
LOKI_GRPC_PORT=9096
```

## 3. Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1
powershell -ExecutionPolicy Bypass -File infra\loki\stop-loki.ps1
```

Проверка:

```powershell
curl.exe -s http://127.0.0.1:3100/ready
```

Ожидается `ready`.

Метрики самого Loki (для любопытства, не путать с Prometheus-контуром):

```powershell
curl.exe -s http://127.0.0.1:3100/metrics | Select-Object -First 5
```

## 4. Что дальше

Пока **не** ставим Alloy / Grafana / Prometheus — только склад логов. Без агента Loki почти пустой: это нормально для этого шага.

## Если не стартует

- Порт занят → `Get-NetTCPConnection -LocalPort 3100,9096`
- Логи → `%LOCALAPPDATA%\Loki\loki.log` и `loki.err.log`
- Бинарник отсутствует → `install-loki.ps1`

## Примечание про Windows Service

Как MinIO: пользовательский процесс, не служба. Автостарт — Task Scheduler / Startup на `start-loki.ps1`, когда понадобится.

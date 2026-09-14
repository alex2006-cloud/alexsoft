# Prometheus (локально, Windows)

См. [ADR-0008](../../artifacts/adr/0008-observability-native-local.md). Нативный `prometheus.exe` — хранилище и сборщик **метрик** для этапа 3. Есть простой веб-UI на том же порту (не путать с Grafana). Docker/Compose — на этапе VPS.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| `prometheus.exe`, `promtool.exe` | `%LOCALAPPDATA%\Prometheus\` |
| TSDB (данные) | `%LOCALAPPDATA%\Prometheus\data\` |
| Конфиг | `infra/prometheus/prometheus.yml` |
| Логи процесса | `%LOCALAPPDATA%\Prometheus\prometheus.log` |

HTTP: `http://127.0.0.1:9090` (порт из `.env` → `PROMETHEUS_PORT`).

## 1. Установка бинарников

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File infra\prometheus\install-prometheus.ps1
```

Скрипт качает официальный релиз Prometheus **v3.14.0** (`prometheus-3.14.0.windows-amd64.zip`) в `%LOCALAPPDATA%\Prometheus`. Повторный запуск не перезаписывает уже скачанные exe.

## 2. `.env`

```
PROMETHEUS_HOST=localhost
PROMETHEUS_PORT=9090
```

## 3. Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1
powershell -ExecutionPolicy Bypass -File infra\prometheus\stop-prometheus.ps1
```

Проверка:

```powershell
curl.exe -s http://127.0.0.1:9090/-/ready
```

Ожидается текст вроде `Prometheus Server is Ready`.

В браузере:

- UI / Graph: http://127.0.0.1:9090
- Targets: http://127.0.0.1:9090/targets — job `prometheus` должен быть **UP**
- Self-metrics: http://127.0.0.1:9090/metrics

Минимальный конфиг скрейпит **сам Prometheus** (`127.0.0.1:9090`). Старт включает `--web.enable-remote-write-receiver`, чтобы **Alloy** мог пушить метрики (`prometheus.remote_write` → `/api/v1/write`).

## 4. Что дальше

Пока **не** ставим Alloy / Grafana. Prometheus уже копит свои метрики — этого достаточно, чтобы позже подключить Grafana datasource и/или remote_write из Alloy.

## Если не стартует

- Порт занят → `Get-NetTCPConnection -LocalPort 9090`
- Логи → `%LOCALAPPDATA%\Prometheus\prometheus.log` и `prometheus.err.log`
- Бинарник отсутствует → `install-prometheus.ps1`

## Примечание про Windows Service

Как Loki/MinIO: пользовательский процесс, не служба. Автостарт — Task Scheduler / Startup на `start-prometheus.ps1`, когда понадобится.

# Grafana Alloy (локально, Windows)

См. [ADR-0008](../../artifacts/adr/0008-observability-native-local.md). Нативный `alloy.exe` — агент сбора **логов и метрик** для этапа 3. Есть свой HTTP UI (отладка компонентов), не путать с Grafana. Docker/Compose — на этапе VPS.

## Пайплайны (текущие)

| Поток | Источник | Куда | Labels / job |
|-------|----------|------|----------------|
| Логи | `%LOCALAPPDATA%\Alloy\demo\app.log` | Loki | `job=alexsoft-demo` |
| Логи | PostgreSQL `data\log\postgresql-*.log` | Loki | `job=postgresql` |
| Метрики | scrape Alloy `:12345/metrics` | Prometheus | `job=alloy` |
| Метрики | Windows CPU (`prometheus.exporter.windows`) | Prometheus | `job=integrations/windows` |

### PostgreSQL change logs

1. Включить логирование изменений (один раз; нужен пароль суперпользователя `postgres`):

```powershell
powershell -ExecutionPolicy Bypass -File infra\postgres\enable-change-logging.ps1
```

Либо перезапустить службу **postgresql-x64-16** от администратора, если в `postgresql.conf` уже стоит `log_statement = 'mod'` (скрипт/правка конфига).

2. Сгенерировать тестовое изменение (роль `alexsoft` из `.env`):

```powershell
powershell -ExecutionPolicy Bypass -File infra\postgres\seed-pg-change.ps1
```

3. В Grafana Explore → Loki:

```
{job="postgresql"} |= "INSERT"
```

### CPU ноутбука

В Grafana Explore → Prometheus:

```
100 - (avg(rate(windows_cpu_time_total{mode="idle"}[1m])) * 100)
```

Значение ≈ процент загрузки CPU (не idle).

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| `alloy.exe` | `%LOCALAPPDATA%\Alloy\` |
| Storage | `%LOCALAPPDATA%\Alloy\data\` |
| Demo log | `%LOCALAPPDATA%\Alloy\demo\app.log` |
| Конфиг | `infra/alloy/config.alloy` |
| Логи процесса | `%LOCALAPPDATA%\Alloy\alloy.log` |

HTTP UI: `http://127.0.0.1:12345` (порт из `.env` → `ALLOY_HTTP_PORT`).

## 1. Установка бинарника

```powershell
powershell -ExecutionPolicy Bypass -File infra\alloy\install-alloy.ps1
```

Релиз Alloy **v1.19.2**, standalone (не Windows Service installer).

## 2. `.env`

```
ALLOY_HOST=localhost
ALLOY_HTTP_PORT=12345
LOKI_PORT=3100
PROMETHEUS_PORT=9090
```

`start-alloy.ps1` сам собирает `LOKI_PUSH_URL` и `PROMETHEUS_REMOTE_WRITE_URL`.

## 3. Зависимости

Перед Alloy должны быть запущены:

```powershell
powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1
powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1
```

Prometheus должен быть с флагом `--web.enable-remote-write-receiver` (есть в актуальном `start-prometheus.ps1`). Если Prometheus поднимали раньше — сделайте `stop` → `start`.

## 4. Запуск / остановка Alloy

```powershell
powershell -ExecutionPolicy Bypass -File infra\alloy\start-alloy.ps1
powershell -ExecutionPolicy Bypass -File infra\alloy\stop-alloy.ps1
```

После смены `config.alloy` или портов в `.env`: **stop → start** (reload не подхватывает новые env).

Проверка агента:

```powershell
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:12345/-/ready
```

Ожидается `200`. UI: http://127.0.0.1:12345

## 5. Демо-лог → Loki

```powershell
powershell -ExecutionPolicy Bypass -File infra\alloy\seed-demo-log.ps1
```

Через несколько секунд в Loki (PowerShell удобнее через URL-encode):

```powershell
$q = [uri]::EscapeDataString('{job="alexsoft-demo"}')
Invoke-RestMethod "http://127.0.0.1:3100/loki/api/v1/query_range?query=$q&limit=5"
```

В Grafana Explore (после datasource Loki): `{job="alexsoft-demo"}`.

## 6. Метрики Alloy → Prometheus

Alloy скрейпит себя и шлёт remote_write. Проверка в Prometheus:

```powershell
curl.exe -s -G "http://127.0.0.1:9090/api/v1/query" --data-urlencode "query=alloy_build_info"
```

Ожидается `status":"success"` и ненулевой результат. В UI: http://127.0.0.1:9090/graph

## Если не работает

- Порт занят → `Get-NetTCPConnection -LocalPort 12345`
- Логи Alloy → `%LOCALAPPDATA%\Alloy\alloy.log`, `alloy.err.log`
- Loki/Prometheus не ready → сначала их `start-*.ps1`
- remote_write 404/отказ → перезапустите Prometheus новым скриптом
- Компоненты красные в UI Alloy → откройте http://127.0.0.1:12345 и смотрите health

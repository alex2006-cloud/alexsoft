# Grafana (локально, Windows)

См. [ADR-0008](../../artifacts/adr/0008-observability-native-local.md). Нативный Grafana OSS — UI для логов (Loki) и метрик (Prometheus) на этапе 3. Порт **3001**, чтобы не спорить с лендингом на `:3000`. Docker/Compose — на этапе VPS.

## Datasources (provisioning)

При каждом старте `start-grafana.ps1` пишет `%LOCALAPPDATA%\Grafana\provisioning\datasources\alexsoft.yml` из шаблона `infra/grafana/provisioning/datasources/alexsoft.yml.template` (порты из `.env`).

| Имя | Тип | URL |
|-----|-----|-----|
| **Prometheus** | prometheus (default) | `http://127.0.0.1:9090` |
| **Loki** | loki | `http://127.0.0.1:3100` |

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| Бинарник + `public/` / `conf/` | `%LOCALAPPDATA%\Grafana\` |
| Данные (SQLite) | `%LOCALAPPDATA%\Grafana\data\` |
| Provisioning | `%LOCALAPPDATA%\Grafana\provisioning\` |
| Логи Grafana | `%LOCALAPPDATA%\Grafana\log\` |
| stdout/stderr процесса | `%LOCALAPPDATA%\Grafana\grafana.out.log` |

UI: `http://127.0.0.1:3001` (порт из `.env` → `GRAFANA_PORT`).

## 1. Установка

```powershell
powershell -ExecutionPolicy Bypass -File infra\grafana\install-grafana.ps1
```

Grafana OSS **v13.2.1**, standalone zip (не MSI).

## 2. `.env`

```
GRAFANA_HOST=localhost
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me
PROMETHEUS_PORT=9090
LOKI_PORT=3100
```

## 3. Зависимости перед просмотром

```powershell
powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1
powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1
powershell -ExecutionPolicy Bypass -File infra\alloy\start-alloy.ps1
powershell -ExecutionPolicy Bypass -File infra\alloy\seed-demo-log.ps1
```

## 4. Запуск / остановка Grafana

```powershell
powershell -ExecutionPolicy Bypass -File infra\grafana\start-grafana.ps1
powershell -ExecutionPolicy Bypass -File infra\grafana\stop-grafana.ps1
```

После смены шаблона datasources: **stop → start**.

Проверка:

```powershell
curl.exe -s http://127.0.0.1:3001/api/health
```

Ожидается `"database":"ok"`.

Логин: http://127.0.0.1:3001 — `admin` / пароль из `.env`.

## 5. Смотрим логи и метрики

### Готовый дашборд (рекомендуется)

В папке **Dashboards → alexsoft** три отдельных дашборда:

| Дашборд | URL |
|---------|-----|
| Laptop CPU | http://127.0.0.1:3001/d/alexsoft-cpu |
| PostgreSQL logs | http://127.0.0.1:3001/d/alexsoft-pg-logs |
| PostgreSQL changes | http://127.0.0.1:3001/d/alexsoft-pg-changes |

Запросы уже сохранены — Explore каждый раз не нужен. Панель changes заполнится после `log_statement=mod`.

### Explore (разовые запросы)

1. http://127.0.0.1:3001/explore  
2. Loki: `{job="postgresql"}`  
3. Prometheus: `100 - (avg(rate(windows_cpu_time_total{mode="idle"}[1m])) * 100)`

Change-логи SQL: `enable-change-logging.ps1` + `seed-pg-change.ps1` — см. [infra/alloy/README.md](../alloy/README.md).

JSON дашборда в репо: `infra/grafana/provisioning/dashboards/json/`.

## Если не стартует / пустой Explore

- Порт занят → `Get-NetTCPConnection -LocalPort 3001`
- Логи → `%LOCALAPPDATA%\Grafana\grafana.out.log`, `grafana.err.log`
- Datasource red → Loki/Prometheus не запущены
- Нет логов → `seed-demo-log.ps1`, подождать ~5 с
- Нет `alloy_build_info` → Alloy + Prometheus с remote_write receiver

## Примечание про Windows Service / MSI

Официальный `.msi` ставит службу. Для учебной локалки alexsoft выбран **zip + пользовательский процесс**.

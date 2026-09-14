# Metabase (локально, Windows)

См. [ADR-0009](../../artifacts/adr/0009-metabase-native-local.md). Нативный BI для этапа 3: OSS **JAR** + Java. UI для вопросов/дашбордов поверх PostgreSQL `alexsoft`. Не путать с Grafana (логи/метрики). Docker/Compose — на этапе VPS.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| `metabase.jar` | `%LOCALAPPDATA%\Metabase\` |
| Application DB (H2) | `%LOCALAPPDATA%\Metabase\` (файлы рядом с JAR) |
| stdout/stderr | `%LOCALAPPDATA%\Metabase\metabase.out.log` / `metabase.err.log` |

UI: `http://127.0.0.1:3002` (порт из `.env` → `METABASE_PORT`). Порт **3000** — лендинг, **3001** — Grafana.

## Зависимости

1. **Java 25+** (рекомендация Metabase: Eclipse Temurin JRE HotSpot).
   ```powershell
   winget install --id EclipseAdoptium.Temurin.25.JRE -e
   java -version
   ```
2. PostgreSQL `alexsoft` уже должен быть доступен (ADR-0004) — подключение datasource делаем **после** первого Setup в UI.

## 1. Установка JAR

```powershell
powershell -ExecutionPolicy Bypass -File infra\metabase\install-metabase.ps1
```

Metabase OSS **v0.63.17**, файл `metabase.jar` (~630 MB).

> **Windows:** `v0.63.16.x` падает при старте (`Illegal char <:>` в пути к JAR). Не откатываться на 0.63.16.

## 2. `.env`

```
METABASE_HOST=127.0.0.1
METABASE_PORT=3002
```

## 3. Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\metabase\start-metabase.ps1
powershell -ExecutionPolicy Bypass -File infra\metabase\stop-metabase.ps1
```

Проверка:

```powershell
curl.exe -s http://127.0.0.1:3002/api/health
```

Ожидается JSON со `"status":"ok"` (или аналогичный healthy-ответ).

Первый старт может занять **1–3 минуты** (инициализация H2).

## 4. Первый Setup (вручную в браузере)

1. Открыть http://127.0.0.1:3002/setup  
2. Создать admin-пользователя  
3. **Sample database** — по желанию (для учёбы можно пропустить)  
4. Data source PostgreSQL подключим отдельным шагом (не в этом README как обязательный блок установки)

## Если не стартует

- Java отсутствует / старая → `java -version` (нужна 25+)
- Порт занят → `Get-NetTCPConnection -LocalPort 3002`
- Логи → `%LOCALAPPDATA%\Metabase\metabase.out.log` и `metabase.err.log`

## Примечание про Windows Service

Как Loki/Grafana: пользовательский процесс, не служба. Автостарт — Task Scheduler на `start-metabase.ps1`, когда понадобится.

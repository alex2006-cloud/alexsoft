# MinIO (локально, Windows)

См. [ADR-0006](../../artifacts/adr/0006-minio-native-local.md). Без Docker — нативный `minio.exe` + встроенная **Console** (веб-GUI) + CLI **`mc`**.

## Статус на машине разработчика

| Компонент | Где |
|-----------|-----|
| `minio.exe`, `mc.exe` | `%LOCALAPPDATA%\MinIO\` |
| Данные | `%LOCALAPPDATA%\MinIO\data\` |
| Логи | `%LOCALAPPDATA%\MinIO\minio.log` |

S3 API: `127.0.0.1:9000`. Console: `http://127.0.0.1:9001`. Бакет по умолчанию: **`alexsoft`**.

Учётные данные — из `.env` (`MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`). Пароль не короче **8 символов**.

## 1. Установка бинарников

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File infra\minio\install-minio.ps1
```

Скрипт качает официальные `minio.exe` и `mc.exe` в `%LOCALAPPDATA%\MinIO`. Повторный запуск не перезаписывает уже скачанные файлы.

Вручную:

- Server: https://dl.min.io/server/minio/release/windows-amd64/minio.exe
- Client: https://dl.min.io/client/mc/release/windows-amd64/mc.exe

## 2. `.env`

```
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-me
MINIO_BUCKET=alexsoft
```

После смены пароля перезапустить MinIO (`stop` → `start`).

## 3. Запуск / остановка

```powershell
powershell -ExecutionPolicy Bypass -File infra\minio\start-minio.ps1
powershell -ExecutionPolicy Bypass -File infra\minio\stop-minio.ps1
```

Проверка API:

```powershell
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:9000/minio/health/live
```

Ожидается `200`.

## 4. Console (GUI)

1. Открыть в браузере: http://127.0.0.1:9001
2. Логин: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` из `.env`.
3. При первом входе подтвердить лицензию (**Acknowledge**).
4. **Buckets** → бакет `alexsoft` (после seed) → объекты в префиксе `demo/`.

Отдельный пакет MinIO Console не нужен — UI встроен в сервер.

## 5. Учебные файлы

Сценарий как у PostgreSQL: одни и те же объекты видны в Console и в `mc`.

```powershell
powershell -ExecutionPolicy Bypass -File infra\minio\seed-demo.ps1
```

Подробности: [demo/README.md](demo/README.md).

## 6. CLI (`mc`)

```powershell
$mc = "$env:LOCALAPPDATA\MinIO\mc.exe"
& $mc ls alexsoft
& $mc ls --recursive alexsoft/alexsoft/demo
& $mc stat alexsoft/alexsoft/demo/docs/hello.md
```

Алиас `alexsoft` создаёт `seed-demo.ps1` (endpoint + ключи из `.env`).

## Если Console не открывается

- Процесс не запущен → `start-minio.ps1`
- Неверный пароль → сверь `.env` (минимум 8 символов) и перезапусти
- Порт занят → `Get-NetTCPConnection -LocalPort 9000,9001`
- Логи → `%LOCALAPPDATA%\MinIO\minio.log` и `minio.err.log`

## Примечание про Windows Service

Как и Memurai: сейчас пользовательский процесс, не служба. Автостарт со входом в Windows — ярлык в Startup или Task Scheduler на `start-minio.ps1`. Полноценная служба — NSSM или Docker, когда понадобится.

## Альтернатива: Docker

Появится Docker Desktop — опциональный сервис можно добавить в `infra/compose/docker-compose.data.yml` отдельным решением. Основной путь локально — этот README.

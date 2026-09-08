# ADR-0006: MinIO — локальная нативная установка (Windows)

- **Статус:** accepted
- **Дата:** 2026-09-08
- **Контекст:** Этап 2 дорожной карты — платформа данных. PostgreSQL (ADR-0004) и Redis/Memurai (ADR-0005) уже стоят нативно. Docker Desktop на машине разработки нет. Нужен S3-совместимый object storage для файлов (будущие RAG-документы, артефакты агентов, загрузки продуктов) до появления потребителей. MinIO официально отдаёт `minio.exe` для Windows; веб-консоль встроена в тот же бинарник.
- **Решение:**
  - **Где:** только локально (Windows), бинарник [MinIO Server](https://dl.min.io/server/minio/release/windows-amd64/minio.exe).
  - **Топология:** один инстанс single-drive, каталог данных `%LOCALAPPDATA%\MinIO\data`, один бакет **`alexsoft`**.
  - **Сеть:** S3 API `127.0.0.1:9000`, Console `127.0.0.1:9001`; в интернет не публикуем; firewall-правило для внешнего доступа не нужно.
  - **Учётные данные:** `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` из `.env` (пароль ≥ 8 символов — требование MinIO).
  - **GUI:** встроенная **MinIO Console** (отдельный пакет Console не ставим).
  - **CLI:** [MinIO Client `mc`](https://dl.min.io/client/mc/release/windows-amd64/mc.exe).
  - **Docker Compose:** не основной путь; при появлении Docker — опциональный сервис можно добавить в `docker-compose.data.yml` отдельным решением.
- **Последствия:**
  - Пошаговая инструкция — `infra/minio/README.md`.
  - На машине разработчика MinIO работает как пользовательский процесс (скрипты `start-minio.ps1` / `stop-minio.ps1`), не как Windows Service.
  - Бинарники и данные живут вне репозитория (`%LOCALAPPDATA%\MinIO\`).
  - VPS/облако и общий бакет для сервисов — позже, отдельный ADR.

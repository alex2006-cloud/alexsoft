# ADR-0005: Redis — локальная нативная установка (Windows / Memurai)

- **Статус:** accepted
- **Дата:** 2026-09-03
- **Контекст:** Этап 2 дорожной карты — платформа данных. PostgreSQL уже стоит нативно (ADR-0004). Docker Desktop на машине разработки нет. Нужен локальный Redis-совместимый кеш до появления потребителей (ai-gateway — этап 5). Официальный путь Redis для Windows без Docker/WSL — [Memurai](https://www.memurai.com/) (партнёр Redis).
- **Решение:**
  - **Где:** только локально (Windows), **Memurai Developer Edition** (Redis 7–совместимый API).
  - **Топология:** один инстанс, порт **6379**, bind на localhost; пароль через `requirepass` = `REDIS_PASSWORD` из `.env`.
  - **Сеть:** в интернет не публикуем; firewall-правило для внешнего доступа не нужно.
  - **Установка:** предпочтительно MSI/`winget`; если MSI падает с 1603 (custom action / temp) — раскладка в `%LOCALAPPDATA%\Memurai` и запуск процессом (`start-memurai.ps1`), см. README.
  - **Клиент GUI:** [Redis Insight](https://redis.io/insight/) (официальный GUI Redis) — просмотр ключей, CLI, настройка.
  - **CLI:** `memurai-cli.exe` из состава Memurai (аналог `redis-cli`).
  - **Docker Compose:** не основной путь; при появлении Docker — опциональный сервис можно добавить в `docker-compose.data.yml` отдельным решением.
- **Последствия:**
  - Пошаговая инструкция — `infra/redis/README.md`.
  - На машине разработчика Memurai может работать как пользовательский процесс (не Windows Service), пока MSI-установщик нестабилен.
  - Memurai Developer — для разработки/тестов; при прод-нагрузке на Windows — Enterprise / Linux Redis (новый ADR).
  - VPS/облако и общий кеш для сервисов — позже, отдельный ADR.

# ADR-0007: Edge — Nginx вместо Caddy; GUI — Nginx Proxy Manager

- **Статус:** accepted
- **Дата:** 2026-09-08
- **Контекст:** В репозитории для публичного лендинга был заложен Caddy (Docker Compose + авто-HTTPS). На VPS (`osipcraft.ru`) фактически уже работает **host Nginx + Certbot**; RAM ~1 ГиБ, Docker нет. Нужен один источник правды по edge и решение по GUI (Nginx Proxy Manager vs aaPanel).
- **Решение:**
  - **Веб-сервер статики:** **Nginx** (не Caddy). Caddy из контура убираем.
  - **Прод сейчас (VPS ~1 ГиБ):** host Nginx + Let’s Encrypt через Certbot. Канонический конфиг — `infra/nginx/osipcraft.ru.conf`. Деплой статики без изменений: rsync в `/var/www/osipcraft` (workflow Landing).
  - **GUI:** **Nginx Proxy Manager (NPM)**, не aaPanel. NPM легче, живёт в Docker Compose, заточен под proxy + SSL для нескольких хостов; aaPanel — тяжёлая hosting-панель с своим стеком, конфликтует с ручным/Docker-контуром и не подходит для 1 ГиБ.
  - **Docker-контур (когда RAM ≥ ~2 ГиБ и есть Docker):** `infra/compose/docker-compose.yml` — сервис `landing` (nginx:alpine, статика) + `npm` (порты 80/443, UI на `127.0.0.1:81`). Публичный TLS и домены — в NPM UI; внутренний upstream `http://landing:80`.
  - На текущем VPS Docker + NPM **не включаем**, пока не будет запаса RAM/swap: риск OOM и простоя работающего сайта.
- **Последствия:**
  - Удалены Caddyfile и сервис Caddy из compose.
  - README в `infra/compose` и `infra/README` описывают host Nginx как прод и compose+NPM как следующий шаг.
  - Переезд прода на NPM = отдельная операция: Docker, остановка host nginx, выпуск/перенос сертификатов в NPM, проверка `:81` только через SSH-туннель.

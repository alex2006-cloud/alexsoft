# Nginx (host на VPS)

Прод edge: **Nginx + Certbot** ([ADR-0007](../../artifacts/adr/0007-edge-nginx-npm.md)).

Канонический сайт: **https://alexsoft.space**. Статика на сервере: `/var/www/osipcraft` (имя каталога историческое).

## Файлы

| Файл | Роль |
|------|------|
| [`alexsoft.space.conf`](alexsoft.space.conf) | Основной сайт: HTTP→HTTPS, www→apex, статика, HSTS |
| [`osipcraft.ru.conf`](osipcraft.ru.conf) | Старый домен: только `301` на `https://alexsoft.space` |

## Применить на VPS

С машины, где есть SSH и актуальный репо (подставь свой ключ при необходимости):

```bash
scp infra/nginx/alexsoft.space.conf root@130.17.1.193:/etc/nginx/sites-available/alexsoft.space
scp infra/nginx/osipcraft.ru.conf root@130.17.1.193:/etc/nginx/sites-available/osipcraft.ru
ssh root@130.17.1.193 'ln -sf /etc/nginx/sites-available/alexsoft.space /etc/nginx/sites-enabled/alexsoft.space && nginx -t && systemctl reload nginx'
```

Сертификаты Let’s Encrypt:

- `/etc/letsencrypt/live/alexsoft.space/`
- `/etc/letsencrypt/live/osipcraft.ru/` (нужен для HTTPS-редиректа со старого домена)

Обновление: `certbot renew` (timer/cron).

Целевая роль edge (раздача статики лендинга и игр, `reverse proxy /app, /api` на кабинет и страницу входа Authentik; JWT проверяет FastAPI, не Nginx — [ADR-0019](../../artifacts/adr/0019-cabinet-ssr-bff-authentik.md)) и IAM — по архитектуре ([ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md)); локально сейчас, не откладывать на VPS.

## Локальный gateway (Windows, нативно)

Папка [`local/`](local/): шаблон конфига [`alexsoft.local.conf`](local/alexsoft.local.conf) и скрипты. Nginx — zip с nginx.org в `%LOCALAPPDATA%\AlexsoftNginx`, порт **8000** ([ADR-0020](../../artifacts/adr/0020-local-iam-gateway-topology.md)).

```powershell
powershell -ExecutionPolicy Bypass -File infra\nginx\local\start-nginx.ps1          # dev: проксирует Next dev (3000, 3010, 3020)
powershell -ExecutionPolicy Bypass -File infra\nginx\local\start-nginx.ps1 -Static  # раздаёт apps/landing/out и apps/games/out
powershell -ExecutionPolicy Bypass -File infra\nginx\local\stop-nginx.ps1
```

| Хост | Куда |
|------|------|
| `http://alexsoft.localhost:8000/` | лендинг; `/games/` игры; `/app/` кабинет (SSR + BFF `/app/api/*`) |
| `http://auth.alexsoft.localhost:8000/` | Authentik (127.0.0.1:9100) |
| любой другой хост на :8000 | `302` на сайт |

Gateway: маршрутизация, `limit_req`, security-заголовки, `X-Request-Id`, JSON access-лог (`logs/access.log`, подхватывается Alloy при необходимости), SSE без буферизации для `/app/`. **JWT не проверяет**; BL (`127.0.0.1:8100`) наружу не проксируется. `/api/` зарезервирован (404). Имена `*.localhost` в Windows обычно резолвятся в loopback сами; запасной вариант — [`local/add-hosts.ps1`](local/add-hosts.ps1) (нужен администратор).

Прод-конфиг для Authentik на VPS готов, но не применён: [`auth.alexsoft.space.conf`](auth.alexsoft.space.conf).

Docker + Nginx Proxy Manager — опционально в `infra/compose/`, не на текущем 1 ГиБ VPS.

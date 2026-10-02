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

Целевая роль edge (JWT Authentik, `reverse proxy /api`) и IAM — этап 6, [ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md).

Docker + Nginx Proxy Manager — опционально в `infra/compose/`, не на текущем 1 ГиБ VPS.

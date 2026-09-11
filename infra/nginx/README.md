# Nginx (host на VPS)

Прод edge для `osipcraft.ru`: **Nginx + Certbot**. Решение — [ADR-0007](../../artifacts/adr/0007-edge-nginx-npm.md).

## Файлы

- `osipcraft.ru.conf` — server blocks: HTTP→HTTPS, www→apex, статика `/var/www/osipcraft`, HSTS и базовые security headers.

## Применить на VPS

```bash
# с машины, где есть SSH на VPS и актуальный репо
scp infra/nginx/osipcraft.ru.conf root@VPS:/etc/nginx/sites-available/osipcraft.ru
ssh root@VPS 'ln -sf /etc/nginx/sites-available/osipcraft.ru /etc/nginx/sites-enabled/osipcraft.ru && nginx -t && systemctl reload nginx'
```

Сертификаты Let’s Encrypt уже должны лежать в `/etc/letsencrypt/live/osipcraft.ru/` (certbot). Обновление сертификатов — `certbot renew` (timer/cron).

Docker + Nginx Proxy Manager — опциональный контур в `infra/compose/`, не на текущем 1 ГиБ VPS.

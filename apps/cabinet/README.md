# alexsoft cabinet

Личный кабинет пользователя и админ-панель. Next.js 16 (App Router, SSR) как **BFF**: браузер ходит только сюда, кабинет с Bearer-токеном пользователя ходит в BL (`apps/api`). Решения: [ADR-0019](../../artifacts/adr/0019-cabinet-ssr-bff-authentik.md), [ADR-0020](../../artifacts/adr/0020-local-iam-gateway-topology.md); контракт BL — [`artifacts/api/bl.openapi.yaml`](../../artifacts/api/bl.openapi.yaml).

## Как устроен вход

1. `GET /app/api/auth/login` — PKCE + `state`/`nonce` (хранятся в Postgres, схема `cabinet`), редирект в Authentik. `?screen=register` ведёт сразу в форму саморегистрации.
2. `GET /app/api/auth/callback` — **обмен кода на сервере** (`openid-client`), токены кладутся в серверную сессию (таблица `cabinet.sessions`, ключ — HMAC от случайного id). В браузере остаётся только httpOnly cookie `alexsoft_session` (path `/app`, SameSite=Lax) с непрозрачным id.
3. Access token обновляется на сервере по refresh token (один refresh на сессию одновременно); если Authentik отказал — сессия удаляется, нужен новый вход.
4. `POST /app/api/auth/logout` — удаляет сессию и завершает SSO-сессию Authentik (RP-initiated logout). Только POST + проверка Origin.

Почему не Auth.js: нужен серверный refresh с сохранением ротируемых токенов и токены только на сервере; с JWT-сессией в cookie обновление из серверных компонентов не персистится. Тот же принцип «токены на сервере» — ADR-0019.

## BFF

`/app/api/bl/v1/*` → BL `/v1/*` с `Authorization: Bearer <access token>`; SSE (`/runs/{id}/events`) стримится насквозь. Не-GET запросы требуют `Origin` своего сайта. Права решает BL (проверка JWT и ролей на его стороне); `roles` в кабинете — только для показа интерфейса.

## Страницы

| Путь | Кто | Что |
|------|-----|-----|
| `/app` | user | агенты, квота, последние запуски |
| `/app/agents/[id]` | user | запуск агента, поток шагов (SSE), беседа в одном thread |
| `/app/runs`, `/app/runs/[id]` | user | история и детали (вывод, trace id) |
| `/app/profile` | user | профиль, роли, квота |
| `/app/admin` … | admin | сводка, пользователи (Authentik), запуски, реестр агентов и квота, ссылки на Authentik / Grafana / Metabase / LiteLLM |

## Запуск и проверка

```powershell
npm install
npm run dev        # :3020, переменные из корневого .env
npm run typecheck
npm test           # чистые функции (safeReturnTo, роли, Origin)
npm run build
```

Нужны корневой `.env` (см. `.env.example`, `infra/authentik/init-env.ps1`), Postgres, Authentik, BL и gateway (OIDC discovery идёт через `AUTH_PUBLIC_URL`).

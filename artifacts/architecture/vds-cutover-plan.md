# План полного переезда на VDS (этап 6)

Источник топологии: [`architecture-in-drawio.drawio`](architecture-in-drawio.drawio) (+ XML-экспорт владельца), [ADR-0015](../adr/0015-target-architecture-stacks.md), [ADR-0019](../adr/0019-cabinet-ssr-bff-authentik.md).

**Режим:** полный cutover runtime на VDS, **включая все БД**. Гибрид «данные на ноутбуке / приложения на VDS» — нет.  
**Lab-мусор:** CrewAI / AutoGen / n8n, демо-агенты и тестовые данные локалки **не переносим**. Первый RAG-агент (БП1) — переносим кодом из monorepo, если поднимется; иначе создаём заново на VDS.  
**Оркестрация day-1:** Docker Compose на VDS (не k3s). k3s / Kafka / РКН — после стабильного контура.

### Хостинг (решение владельца, 2026-10-26)

| Параметр | Выбор |
|----------|--------|
| Провайдер / локация | Fornex, **Германия** (облачные LLM — зарубежные) |
| Домен | `alexsoft.space` (DNS на Fornex; новый VPS — тот же IP/DNS, если Fornex сохранит) |
| Стартовый тариф | Конфигуратор Fornex: **2 vCPU / 6 GB RAM / диск см. ниже**, x86-64, от 2.1 GHz (~1638 ₽ + диск) |
| Диск | **Не 20 GB** — мало под Docker-образы + Postgres/MinIO/Qdrant. Цель заказа: **≥40 GB** (лучше **60–80 GB** NVMe Base/Fast) |
| ОС | Ubuntu 24.04 LTS, **без панели** |
| Сеть | **300 Мбит/с**, IP **общие**, группа размещения **не нужна** |
| Старый VPS | Данные / сертификаты / конфиги **потеряны** — всё с нуля (TLS заново через Let's Encrypt) |
| Бэкапы | Пока **на ноутбук** (не панель Fornex); позже — свой скрипт dump/volume |
| День 1 scope | По успеваемости; минимум — фундамент + лендинг |

**6 GB RAM** — достаточно для лёгкого day-1 (периметр + данные + cabinet/BL + LiteLLM/RAG по очереди; без Dify/тяжёлого BI сразу).  
**Диск 20 GB** — риск: образы Authentik/Postgres/Qdrant/MinIO съедят место быстро → при заказе поднять до **≥40 GB**.

### 1a (устарело для 6 GB)

Фаза «только тонкий срез из‑за 2 GB» больше не нужна; при 6 GB можно идти к фазам 2–4 после фундамента. Диск всё равно контролировать (`df -h`).

**Shared vs dedicated IP:** для `alexsoft.space` (один сайт, свой VPS, обычный HTTPS) бери **общие IP** — дешевле и нормально. Выделенный IP нужен позже, если появятся: своя почта с сервера, требования «белый» IP у банка/API, или соседние шаред-IP ловят blocklist. Сейчас — не брать.

---

## Что поднимаем на VDS (по swimlane схемы)

| Зона | Узлы | День 1 |
|------|------|--------|
| Периметр | Nginx, Authentik, статика лендинг+игры | да |
| Приложения | Cabinet (Next.js SSR), BL FastAPI | да |
| Данные | PostgreSQL, MinIO, Qdrant, Redis | да (с нуля или dump — см. ниже) |
| Шина | RabbitMQ | да (целевой путь BL → Agent Platform) |
| ИИ | LiteLLM, RAG (`apps/rag`), Agent Platform (LangGraph; Dify — по желанию позже) | да (минимум без Studio/LangFlow UI) |
| Guardrails | LLM Guard | после рабочего БК1 |
| Observability | Alloy, Loki, Prometheus, Grafana | после приложений |
| BI | Metabase | после Postgres |
| Внешнее | DeepSeek/Qwen/…, embedding, LangSmith | ключи в `.env` / GitHub Secrets |
| Поставка | Cursor → GitHub → Actions → VDS | CI деплой вместо ручных правок на сервере |
| Не на VDS | agent2, agent3, n8n, Memurai, Windows-native бинарники | остаются lab / выкидываем |

---

## Принципы данных

| Стор | Стратегия | Почему |
|------|-----------|--------|
| **PostgreSQL** | Новый инстанс на VDS + **миграции схем** из кода (`bl`, кабинет/сессии если есть). **Authentik — отдельная БД; пользователей завести заново** (dump не делаем). Demo/seed локалки не тащить. | Решение владельца (2026-10-26) |
| **Redis** | Пустой Redis (не Memurai). Кэш AI не мигрируем | Кэш эфемерный |
| **MinIO** | Новый бакет(ы). Корпус для RAG: пусто или later + ingest с git/`kb-sync` | Воспроизводимо |
| **Qdrant** | Пустые коллекции; **переиндексация только по команде владельца** | Не гоняем embeddings без явного «go» |
| **RabbitMQ** | С нуля | Нет ценных очередей локально |

Критерий «БД переехали»: приложения на VDS читают/пишут **только** VDS Postgres/MinIO/Qdrant/Redis; ноутбук не в runtime-пути.

---

## Фазы (порядок жёсткий)

### 0. Решения и заготовка

- [x] Домен/поддомены (2026-10-28): `alexsoft.space` / `www` — лендинг+игры; `alexsoft.space/app` — кабинет; `auth.alexsoft.space` — Authentik; внутренние сервисы только Docker/`127.0.0.1`.
- [x] Скелет Compose VDS: [`infra/compose/vds/`](../../infra/compose/vds/) + `/etc/alexsoft/.env` на сервере.
- [x] ADR cutover: [ADR-0021](../adr/0021-vds-full-cutover.md).
- [x] Firewall ufw 22/80/443; Nginx HTTP-stub + certbot установлены на VDS.
- [x] DNS: A `alexsoft.space`, `www`, `auth` → `31.172.71.231` (apex починен после отвязки хостинга reg.ru Host-0).
- [x] TLS Let's Encrypt: `alexsoft.space`+`www` (один сертификат), `auth.alexsoft.space` (2026-10-29).
- ~~Бэкапы volume~~ — исключены на старте (решение владельца).

### 1. Фундамент VDS

- [x] SSH-ключи, обновления, Docker Engine + Compose plugin. (2026-10-28: Ubuntu 26.04, Docker 29.9 / Compose 5.6, `hello-world` OK; ufw 22/80/443)
- [x] Каталоги данных (`/var/lib/alexsoft/...`), `.env` вне git (`/etc/alexsoft/.env`, `/var/www/alexsoft`).
- [x] Smoke HTTP-заглушка Nginx на VDS (ответ по `http://31.172.71.231/`). HTTPS — после DNS + certbot (см. фазу 0).

### 2. Плоскость данных (пустая, но «боевая»)

Поднять и прогнать health (`infra/compose/vds/`, секреты `/etc/alexsoft/.env`):

1. [x] PostgreSQL — healthy (`127.0.0.1:5432`)
2. [x] Redis — healthy (`127.0.0.1:6379`)
3. [x] MinIO — Chainguard image, health 200 (`127.0.0.1:9000` / `:9001`; volume uid 65532)
4. [x] Qdrant — up (`127.0.0.1:6333`)
5. [x] RabbitMQ — healthy (`127.0.0.1:5672` / management `:15672` только localhost)

Пока без миграции контента / ingest — только инстансы и volumes. (2026-10-28)

### 3. Периметр + IAM

- [x] Nginx: HTTP/HTTPS stub лендинга (`www` TLS); `/app` → 503 до фазы 4; Authentik на `auth.alexsoft.space` (TLS). Apex `alexsoft.space` — DNS ещё старый IP.
- [x] Authentik Compose на VDS (`docker-compose.authentik.yml` + DB `authentik` в Postgres); blueprint OIDC `alexsoft-cabinet`, JWKS OK. (2026-10-28)
- [x] Админ bootstrap: пользователь **`akadmin`**, пароль в `/etc/alexsoft/.env` → `AUTHENTIK_BOOTSTRAP_PASSWORD` (на сервере). Тестового user — через UI enrollment или Admin после входа.
- [x] Полный Nginx под кабинет (`/app` → `:3020`) — 2026-10-29 (фаза 4).
- [x] TLS на apex `alexsoft.space` (+ www) — 2026-10-29.

### 4. Приложения

- [x] BL API (`apps/api`): Compose `bl-api`, схема `bl`, JWT/JWKS via `authentik-server`, порт `127.0.0.1:8100` (2026-10-29).
- [x] Cabinet SSR (`apps/cabinet`): Compose `cabinet`, OIDC → `auth.alexsoft.space`, BFF → `bl-api`, порт `127.0.0.1:3020` (2026-10-29).
- [x] CI: статика — [`.github/workflows/landing.yml`](../../.github/workflows/landing.yml) → VDS `/var/www/alexsoft`; образы cabinet/api — [`.github/workflows/apps.yml`](../../.github/workflows/apps.yml) → GHCR → `deploy-apps.sh` (2026-10-29).
- [x] Smoke БК1 без AI: логин → список агентов (echo + langgraph stubs) — 2026-10-29.

### 5. ИИ-контур

- [ ] LiteLLM + ключи провайдеров + `text-embedding-3-small`.
- [ ] RAG (`apps/rag`) → MinIO + Qdrant + LiteLLM.
- [ ] Ingest корпуса (из git / MinIO) → коллекции `project-docs` / `project-code` (или новые имена).
- [ ] Agent Platform: LangGraph runtime (код из `apps/agent1`); Studio/LangFlow/Dify — не блокер cutover.
- [ ] Провод RabbitMQ: BL `publish` → Agent `consume run` (убрать прямой HTTP BL→Agent как временный).
- [ ] Агент Q&A по проекту: поднять существующий граф **или** новый — критерий: прогон + ответ с источниками.
- [ ] LLM Guard — после зелёного прогона без него.

### 6. Наблюдаемость и BI

- [ ] Alloy → Loki / Prometheus → Grafana (базовые дашборды host + контейнеры).
- [ ] Metabase → read-only к Postgres.
- [ ] LangSmith: ключ, трейсы с Agent/LiteLLM.

### 7. Cutover и выключение локалки как runtime

- [ ] DNS/трафик только на VDS.
- [ ] Финальные бэкапы volume (Postgres dump, MinIO, Qdrant snapshot «на всякий»).
- [ ] Ноутбук: остановить Postgres/Memurai/MinIO/Qdrant/Authentik/… как **серверы продукта**; оставить только Cursor + git.
- [ ] Обновить ROADMAP: этап 6 planning ✓, фазы внедрения по факту.

### 8. После стабилизации (не day-1)

- NPM при нехватке удобства Nginx, Portainer, k3s, Kafka, заявка РКН — только если появятся ПДн субъектов РФ в проде.

---

## Что сознательно не делаем при переезде

- Не копируем lab: agent2, agent3, n8n, локальные demo bucket/таблицы.
- Не тащим Memurai — только Redis.
- Не поднимаем k3s «заодно».
- Не публикуем LiteLLM / RAG / BL / Qdrant / RabbitMQ в интернет — только через Nginx (статика + cabinet + Authentik).

---

## Критерий успеха этапа 6 (минимум)

Сторонний пользователь: **лендинг (VDS) → логин Authentik → кабинет → запуск Q&A-агента по проекту → ответ с опорой на корпус в Qdrant**, при этом Postgres/MinIO/Qdrant/Redis/RabbitMQ живут на VDS. Trace в LangSmith — желательно, не блокер первого зелёного прогона.

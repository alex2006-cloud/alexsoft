# Кабинет (`apps/cabinet`)

Next.js SSR + BFF под `basePath: /app`, порт **3020** ([ADR-0019](../../artifacts/adr/0019-cabinet-ssr-bff-authentik.md), [ADR-0020](../../artifacts/adr/0020-local-iam-gateway-topology.md)). Код и описание — [`apps/cabinet`](../../apps/cabinet/README.md).

```powershell
cd apps\cabinet
npm install
npm run dev          # http://127.0.0.1:3020/app (в браузере ходите через gateway: http://alexsoft.localhost:8000/app)
```

Порядок подъёма локально (всё нативно, кроме Authentik): Postgres → Authentik (`infra\authentik`) → BL (`infra\api\start-api.ps1`) → кабинет → gateway (`infra\nginx\local\start-nginx.ps1`). Одной командой: `scripts\dev-up.ps1 -WithAuth -WithApi -WithCabinet -WithGateway -WithLanding`.

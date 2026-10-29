# Cabinet (Next.js SSR). Build from repo root:
#   docker build -f apps/cabinet/Dockerfile -t alexsoft-cabinet .
FROM node:22-bookworm-slim AS deps
WORKDIR /repo/apps/cabinet
COPY apps/cabinet/package.json apps/cabinet/package-lock.json ./
RUN npm ci

FROM node:22-bookworm-slim AS builder
WORKDIR /repo/apps/cabinet
COPY --from=deps /repo/apps/cabinet/node_modules ./node_modules
COPY apps/cabinet/ ./
# next.config loadEnvConfig(../..) → /repo/.env (optional; runtime env wins)
RUN mkdir -p /repo && printf '\n' > /repo/.env
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3020

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=builder /repo/apps/cabinet/public ./public
COPY --from=builder --chown=nextjs:nodejs /repo/apps/cabinet/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/apps/cabinet/.next/static ./.next/static

USER nextjs
EXPOSE 3020
CMD ["node", "server.js"]

import { Pool } from "pg";

// Sessions live in Postgres (schema "cabinet"): tokens stay on the server, the browser only holds an opaque id.

const DDL = `
CREATE SCHEMA IF NOT EXISTS cabinet;
CREATE TABLE IF NOT EXISTS cabinet.sessions (
  key        text PRIMARY KEY,
  data       jsonb       NOT NULL,
  expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expires_idx ON cabinet.sessions (expires_at);
`;

type G = typeof globalThis & { __cabinetPool?: Pool; __cabinetReady?: Promise<void> };
const g = globalThis as G;

export function pool(): Pool {
  if (!g.__cabinetPool) {
    g.__cabinetPool = new Pool({
      host: process.env.POSTGRES_HOST === "localhost" ? "127.0.0.1" : process.env.POSTGRES_HOST || "127.0.0.1",
      port: Number(process.env.POSTGRES_PORT || 5432),
      database: process.env.POSTGRES_DB || "alexsoft",
      user: process.env.POSTGRES_USER || "alexsoft",
      password: process.env.POSTGRES_PASSWORD,
      max: 5,
    });
  }
  return g.__cabinetPool;
}

export async function ready(): Promise<Pool> {
  g.__cabinetReady ??= pool()
    .query(DDL)
    .then(() => undefined)
    .catch((e) => {
      g.__cabinetReady = undefined;
      throw e;
    });
  await g.__cabinetReady;
  return pool();
}

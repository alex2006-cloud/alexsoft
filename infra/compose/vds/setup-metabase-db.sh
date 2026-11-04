#!/usr/bin/env bash
# Create Metabase app DB + read-only analytics role in alexsoft Postgres.
set -euo pipefail
ENV_FILE="${ENV_FILE:-/etc/alexsoft/.env}"
# shellcheck disable=SC1090
set -a && . "$ENV_FILE" && set +a

: "${POSTGRES_USER:?}"
: "${POSTGRES_DB:?}"
: "${METABASE_DB_PASSWORD:?set METABASE_DB_PASSWORD in /etc/alexsoft/.env}"
: "${METABASE_RO_PASSWORD:?set METABASE_RO_PASSWORD in /etc/alexsoft/.env}"

MB_USER="${METABASE_DB_USER:-metabase}"
RO_USER="${METABASE_RO_USER:-metabase_ro}"

docker exec -i alexsoft-vds-postgres-1 \
  env PGPASSWORD="$POSTGRES_PASSWORD" \
  psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${MB_USER}') THEN
    CREATE ROLE ${MB_USER} LOGIN PASSWORD '${METABASE_DB_PASSWORD}';
  ELSE
    ALTER ROLE ${MB_USER} WITH LOGIN PASSWORD '${METABASE_DB_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${RO_USER}') THEN
    CREATE ROLE ${RO_USER} LOGIN PASSWORD '${METABASE_RO_PASSWORD}';
  ELSE
    ALTER ROLE ${RO_USER} WITH LOGIN PASSWORD '${METABASE_RO_PASSWORD}';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE metabase OWNER ${MB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec

GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${RO_USER};
SQL

docker exec -i alexsoft-vds-postgres-1 \
  env PGPASSWORD="$POSTGRES_PASSWORD" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 <<SQL
GRANT USAGE ON SCHEMA public TO ${RO_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${RO_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${RO_USER};

DO \$\$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'bl') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA bl TO ${RO_USER}';
    EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA bl TO ${RO_USER}';
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA bl GRANT SELECT ON TABLES TO ${RO_USER}';
  END IF;
END
\$\$;
SQL

echo "OK: metabase DB + ${RO_USER} ready"

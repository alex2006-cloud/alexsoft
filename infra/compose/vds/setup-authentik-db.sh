#!/usr/bin/env bash
# Create Authentik role+DB inside alexsoft-vds Postgres. Run on VDS as root.
set -euo pipefail
set -a
# shellcheck disable=SC1091
. /etc/alexsoft/.env
set +a

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" alexsoft-vds-postgres-1 \
  psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authentik') THEN CREATE ROLE authentik LOGIN PASSWORD '${AUTHENTIK_DB_PASSWORD}'; ELSE ALTER ROLE authentik WITH LOGIN PASSWORD '${AUTHENTIK_DB_PASSWORD}'; END IF; END \$\$;"

EXISTS=$(docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" alexsoft-vds-postgres-1 \
  psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='authentik'")
if [[ "$EXISTS" != "1" ]]; then
  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" alexsoft-vds-postgres-1 \
    psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE authentik OWNER authentik;"
fi

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" alexsoft-vds-postgres-1 \
  psql -U "$POSTGRES_USER" -d postgres -c "\du authentik" -c "\l authentik"
echo "AUTHENTIK_DB_OK"

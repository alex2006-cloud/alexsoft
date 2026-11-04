#!/usr/bin/env bash
# Phase 7: backup VDS data plane to /var/backups/alexsoft/<stamp>/
# Postgres dump + MinIO tar + Qdrant snapshot API (best-effort).
set -euo pipefail

ENV_FILE="${ENV_FILE:-/etc/alexsoft/.env}"
# shellcheck disable=SC1090
set -a && . "$ENV_FILE" && set +a

: "${POSTGRES_USER:?}"
: "${POSTGRES_DB:?}"
: "${POSTGRES_PASSWORD:?}"

STAMP="${STAMP:-$(date -u +%Y%m%dT%H%MZ)}"
ROOT="${BACKUP_ROOT:-/var/backups/alexsoft}"
DEST="${ROOT}/${STAMP}"
mkdir -p "$DEST"
chmod 700 "$ROOT" "$DEST"

echo "=== backup → $DEST ==="

echo "--- postgres ---"
docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" alexsoft-vds-postgres-1 \
  pg_dumpall -U "$POSTGRES_USER" --clean --if-exists \
  | gzip -c > "${DEST}/postgres-all.sql.gz"
ls -lh "${DEST}/postgres-all.sql.gz"

echo "--- minio volume ---"
# Stop writes briefly not required for day-1; consistent enough for «на всякий».
tar -C /var/lib/alexsoft -czf "${DEST}/minio-data.tar.gz" minio
ls -lh "${DEST}/minio-data.tar.gz"

echo "--- qdrant snapshot ---"
QDIR="${DEST}/qdrant"
mkdir -p "$QDIR"
# List collections and create snapshots via REST (localhost only).
cols=$(curl -fsS http://127.0.0.1:6333/collections | python3 -c 'import sys,json; d=json.load(sys.stdin); print(" ".join(c["name"] for c in d.get("result",{}).get("collections",[])))' || true)
if [[ -z "${cols:-}" ]]; then
  echo "WARN: no qdrant collections or API down — copying storage dir instead"
  tar -C /var/lib/alexsoft -czf "${DEST}/qdrant-storage.tar.gz" qdrant
  ls -lh "${DEST}/qdrant-storage.tar.gz"
else
  for c in $cols; do
    echo "snapshot collection=$c"
    snap=$(curl -fsS -X POST "http://127.0.0.1:6333/collections/${c}/snapshots" | python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["name"])')
    # download snapshot file from container volume path if exposed; else leave name recorded
    echo "$c $snap" >> "${DEST}/qdrant-snapshots.txt"
    # Prefer copying from host volume after snapshot created in-container
    host_snap=$(find /var/lib/alexsoft/qdrant -type f -name "$snap" 2>/dev/null | head -n1 || true)
    if [[ -n "$host_snap" ]]; then
      cp -a "$host_snap" "${QDIR}/"
    else
      docker exec alexsoft-vds-qdrant-1 sh -c "find /qdrant/storage -name '$snap' -print" \
        | while read -r p; do
            docker cp "alexsoft-vds-qdrant-1:${p}" "${QDIR}/" || true
          done
    fi
  done
  # Also archive whole storage for restore simplicity
  tar -C /var/lib/alexsoft -czf "${DEST}/qdrant-storage.tar.gz" qdrant
  ls -lh "${DEST}/qdrant-storage.tar.gz" "${QDIR}" || true
fi

echo "--- redis RDB (optional) ---"
docker exec alexsoft-vds-redis-1 redis-cli -a "$REDIS_PASSWORD" --no-auth-warning BGSAVE >/dev/null || true
sleep 2
docker cp alexsoft-vds-redis-1:/data/dump.rdb "${DEST}/redis-dump.rdb" 2>/dev/null || echo "WARN: redis dump skipped"

cat > "${DEST}/MANIFEST.txt" <<EOF
stamp=${STAMP}
host=$(hostname)
created_utc=$(date -u +%Y-%m-%dT%H:%MZ)
postgres=postgres-all.sql.gz
minio=minio-data.tar.gz
qdrant=qdrant-storage.tar.gz (+ collection snapshots if any)
redis=redis-dump.rdb (best-effort)
EOF

du -sh "$DEST"
echo "OK: backup $DEST"

#!/usr/bin/env bash
set -euo pipefail
cd /opt/alexsoft
tar -xf /tmp/phase6-obs.tar
sed -i 's/\r$//' infra/compose/vds/setup-metabase-db.sh \
  infra/compose/vds/enable-langsmith.sh \
  infra/compose/vds/smoke-obs.sh \
  infra/compose/vds/smoke-metabase.sh \
  infra/compose/vds/bootstrap-phase6.sh || true
chmod +x infra/compose/vds/*.sh

gen() { openssl rand -base64 24 | tr -d '/+=' | head -c 28; }
ENV=/etc/alexsoft/.env
touch "$ENV"
chmod 600 "$ENV"
grep -q '^GRAFANA_ADMIN_PASSWORD=' "$ENV" || echo "GRAFANA_ADMIN_PASSWORD=$(gen)" >> "$ENV"
grep -q '^GRAFANA_ADMIN_USER=' "$ENV" || echo 'GRAFANA_ADMIN_USER=admin' >> "$ENV"
grep -q '^GRAFANA_PORT=' "$ENV" || echo 'GRAFANA_PORT=3001' >> "$ENV"
grep -q '^METABASE_PORT=' "$ENV" || echo 'METABASE_PORT=3002' >> "$ENV"
grep -q '^METABASE_DB_USER=' "$ENV" || echo 'METABASE_DB_USER=metabase' >> "$ENV"
grep -q '^METABASE_DB_PASSWORD=' "$ENV" || echo "METABASE_DB_PASSWORD=$(gen)" >> "$ENV"
grep -q '^METABASE_RO_USER=' "$ENV" || echo 'METABASE_RO_USER=metabase_ro' >> "$ENV"
grep -q '^METABASE_RO_PASSWORD=' "$ENV" || echo "METABASE_RO_PASSWORD=$(gen)" >> "$ENV"

grep -E '^(GRAFANA_|METABASE_|LANGSMITH_)' "$ENV" | sed 's/PASSWORD=.*/PASSWORD=***/;s/API_KEY=.*/API_KEY=***/' || true

if ! swapon --show | grep -q .; then
  if [[ ! -f /swapfile ]]; then
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
  fi
  swapon /swapfile || true
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo SWAP_ENABLED
fi
free -h

mkdir -p /var/lib/alexsoft/{loki,prometheus,grafana,alloy}
# Loki image runs as 10001; Prometheus nobody; Grafana 472
chown -R 10001:10001 /var/lib/alexsoft/loki || true
chown -R 65534:65534 /var/lib/alexsoft/prometheus || true
chown -R 472:0 /var/lib/alexsoft/grafana || true
echo SYNC_OK

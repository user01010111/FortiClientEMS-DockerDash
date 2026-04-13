#!/bin/sh
set -eu

escape_sed() {
  printf '%s' "$1" | sed 's/[\/&]/\\&/g'
}

GF_ADMIN_PASSWORD_ESCAPED="$(escape_sed "${GF_ADMIN_PASSWORD:-}")"

sed \
  -e "s/__GF_ADMIN_PASSWORD__/${GF_ADMIN_PASSWORD_ESCAPED}/g" \
  /etc/prometheus/prometheus.yml.tmpl > /tmp/prometheus.yml

exec /bin/prometheus \
  --config.file=/tmp/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/usr/share/prometheus/console_libraries \
  --web.console.templates=/usr/share/prometheus/consoles

#!/bin/sh
set -eu
# Reuse the pinned exporter's SQL collector for the PG18 fields its native collectors omit.
cat /etc/postgres-exporter/queries-global.yml /etc/postgres-exporter/queries-database.yml > /tmp/queries.yml
exec /bin/postgres_exporter "$@"

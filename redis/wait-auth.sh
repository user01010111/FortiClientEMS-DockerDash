#!/bin/sh
set -e

# The vendor entrypoint starts Redis without authentication if deploy has
# not populated this shared file yet. Docker restart policies do not wait
# for Compose dependencies after a host reboot.
while :; do
    if [ -r /db/.env ]; then
        . /db/.env
        if [ -n "${EMS_REDIS_PASSWORD:-}" ]; then
            exec docker-entrypoint.sh redis-server --requirepass "$EMS_REDIS_PASSWORD"
        fi
    fi
    sleep 2
done

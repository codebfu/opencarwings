#!/usr/bin/env bash

set -euo pipefail

cd /app

python manage.py migrate
if [ -w "/app/staticfiles" ]; then
  python manage.py collectstatic --noinput
else
  echo "WARNING: /app/staticfiles is not writable for UID $(id -u). Skipping collectstatic."
  echo "WARNING: Fix ownership (APP_UID/APP_GID or chown) to re-enable collectstatic."
fi
if [ "${ENABLE_CRON:-1}" = "1" ]; then
  /usr/sbin/crond -f -l 8 &
fi
(python manage.py tcuserver 0.0.0.0; [ "$?" -lt 2 ] && kill "$$") &
(daphne -b 0.0.0.0 -p 8000 --access-log - "$@" carwings.asgi:application; [ "$?" -lt 2 ] && kill "$$") &
wait

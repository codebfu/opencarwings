#!/usr/bin/env bash

set -euo pipefail

cd /app

python manage.py migrate
python manage.py collectstatic --noinput
if [ "${ENABLE_CRON:-1}" = "1" ]; then
  /usr/sbin/crond -f -l 8 &
fi
(python manage.py tcuserver 0.0.0.0; [ "$?" -lt 2 ] && kill "$$") &
(daphne -b 0.0.0.0 -p 8000 --access-log - "$@" carwings.asgi:application; [ "$?" -lt 2 ] && kill "$$") &
wait

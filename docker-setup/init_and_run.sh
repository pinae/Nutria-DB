#!/usr/bin/env bash
set -e
export PATH="/opt/venv/bin:$PATH"
cd /app/nutriaDB
python manage.py wait_for_db
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py initadmin
python manage.py initial_data
exec gunicorn nutriaDB.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --access-logfile - \
    --error-logfile -

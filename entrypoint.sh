#!/bin/bash

echo "Collecting static files"
python manage.py collectstatic --no-input

echo "Applying migrations"
python manage.py migrate

echo "Starting the server, celery and bot..."
exec "$@"

celery -A core worker --loglevel=info &  celery -A core beat --loglevel=info &

gunicorn --bind 0.0.0.0:8000 core.wsgi:application & python manage.py run_telegram_bot
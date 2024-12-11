#!/bin/bash

echo "Collecting static files"
python manage.py collectstatic --no-input

echo "Applying migrations"
python manage.py migrate

echo "Running tests"
python manage.py test

echo "Starting the server, celery and bot..."
exec "$@"

# TODO move celery starting commands to docker-compose files
#celery -A core.celery worker --loglevel=info &  celery -A core beat --loglevel=info &

gunicorn --bind 0.0.0.0:8000 core.wsgi:application & python manage.py run_telegram_bot
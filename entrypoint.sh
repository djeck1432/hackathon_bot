#!/bin/bash

echo "Collecting static files"
python manage.py collectstatic --no-input

echo "Applying migrations"
python manage.py migrate

echo "Creating superuser"
python manage.py create_superuser

echo "Starting the server and bot..."
exec "$@"

gunicorn --bind 0.0.0.0:8000 core.wsgi:application & python -m tracker.telegram.bot
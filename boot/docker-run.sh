#!/bin/bash

source /opt/venv/bin/activate

cd /code

python manage.py vendor_pull
python manage.py collectstatic --no-input

RUN_PORT=${PORT:-8000}
RUN_HOST=${HOST:-0.0.0.0}

# Run migrations on Neon
python manage.py migrate --no-input

# Create a superuser
python manage.py createsuperuser --no-input --username admin --email admin@example.com --password qwer

# Start Django server
python manage.py runserver $RUN_HOST:$RUN_PORT

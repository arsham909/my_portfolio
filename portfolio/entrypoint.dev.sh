#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --no-input

echo "Starting Django devserver..."
exec python manage.py runserver 0.0.0.0:8000

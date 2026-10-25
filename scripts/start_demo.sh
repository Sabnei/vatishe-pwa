#!/bin/sh
# Borra TODO y carga los datos de prueba.
set -e
python manage.py migrate --noinput
python manage.py flush --noinput
python manage.py seed_demo
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
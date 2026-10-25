#!/bin/sh
# Borra TODO y crea solo el administrador real (para entregar al cliente).
set -e
python manage.py migrate --noinput
python manage.py flush --noinput
python manage.py createsuperuser --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
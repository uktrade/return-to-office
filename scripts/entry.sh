#!/bin/sh -e

python manage.py migrate --noinput

python manage.py compilescss

python manage.py collectstatic --noinput

gunicorn config.wsgi:application \
  --config config/gunicorn.py \
  --bind 0.0.0.0:$PORT \
  --timeout 300 \
  --log-file -

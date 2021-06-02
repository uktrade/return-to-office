#!/bin/sh -e

python manage.py migrate --noinput

python manage.py compilescss

python manage.py collectstatic --noinput

python config/app.py

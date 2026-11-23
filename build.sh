#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# creates login user from DJANGO_SUPERUSER_* env vars; fails harmlessly if it exists
python manage.py createsuperuser --noinput || true

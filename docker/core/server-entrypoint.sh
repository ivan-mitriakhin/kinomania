#!/bin/sh

until cd /app/core
do
    echo "Waiting for server volume..."
done

python manage.py collectstatic --noinput

# python manage.py createsuperuser --noinput

gunicorn core.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4

# for debug
#python manage.py runserver 0.0.0.0:8000
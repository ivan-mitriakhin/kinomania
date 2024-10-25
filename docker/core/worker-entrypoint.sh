#!/bin/sh

until cd /app/core
do
    echo "Waiting for server volume..."
done

python -m celery -A core worker --loglevel=info -n worker1@%n --uid=nobody --gid=nogroup --pool=threads
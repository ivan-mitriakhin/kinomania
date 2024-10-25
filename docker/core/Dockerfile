FROM python:3.10.6

RUN apt-get update -y && \
    apt-get install -y netcat

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install gunicorn
ADD ./requirements.txt /app/
RUN pip install -r requirements.txt

ADD ./core /app/core
ADD ./docker /app/docker

RUN chmod +x /app/docker/core/worker-entrypoint.sh
RUN chmod +x /app/docker/core/server-entrypoint.sh
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.8 python3.8-dev python3-pip python-is-python3

WORKDIR /app
ADD ./mercury/requirements.txt /app/mercury/

RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r mercury/requirements.txt

ADD ./mercury/apps /app/mercury/apps
ADD ./mercury/server /app/mercury/server
ADD ./mercury/manage.py /app/mercury/
ADD ./docker /app/docker

RUN chmod +x /app/docker/mercury/entrypoint.sh

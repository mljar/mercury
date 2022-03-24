FROM ubuntu:20.04
ARG GITHUB_TOKEN
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.8 python3.8-dev python3-pip python-is-python3 git

WORKDIR /app
ADD ./mercury/requirements.txt /app/mercury/

RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r mercury/requirements.txt

# install Pro features if GITHUB_TOKEN is set
RUN if [ -z "${GITHUB_TOKEN}" ] ; then \
        echo "Skip Pro features installation." && \
        echo "Please visit https://mljar.com/pricing for Pro features details." ; \
    else \
        echo "Install Pro features ..." && \
        pip install -e git+https://${GITHUB_TOKEN}@github.com/mljar/mercury-pro.git@main#egg=pro ; \
    fi

ADD ./mercury/apps /app/mercury/apps
ADD ./mercury/server /app/mercury/server
ADD ./mercury/manage.py /app/mercury/
ADD ./docker /app/docker

RUN chmod +x /app/docker/mercury/entrypoint.sh

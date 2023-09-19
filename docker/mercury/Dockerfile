FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.8 python3.8-dev python3-pip python-is-python3 git gconf-service \
            libasound2 libatk1.0-0 libatk-bridge2.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 \ 
            libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 \ 
            libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
            libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 \ 
            lsb-release xdg-utils wget libcairo-gobject2 libxinerama1 libgtk2.0-0 libpangoft2-1.0-0 libthai0 libpixman-1-0 \ 
            libxcb-render0 libharfbuzz0b libdatrie1 libgraphite2-3 libgbm1 \
            libpq-dev libarchive13 

# Install Miniconda using official installer script
RUN wget -qO /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

ENV PATH="/opt/conda/bin:${PATH}"

WORKDIR /app
ADD ./mercury/requirements.txt /app/mercury/

RUN conda install --yes mamba -c conda-forge
RUN mamba install --yes python=3.8 --file mercury/requirements.txt -c conda-forge
RUN mamba install --yes gunicorn psycopg2 daphne -c conda-forge
RUN mamba install --yes mercury -c conda-forge

ADD ./mercury/apps /app/mercury/apps
ADD ./mercury/server /app/mercury/server
ADD ./mercury/templates /app/mercury/templates
ADD ./mercury/*.py /app/mercury/
ADD ./mercury/widgets /app/mercury/widgets
ADD ./docker /app/docker

RUN chmod +x /app/docker/mercury/entrypoint.sh

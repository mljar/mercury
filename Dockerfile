# Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

COPY dist/mercury_dev-0.3.0-py3-none-any.whl .
RUN pip install ./mercury_dev-0.3.0-py3-none-any.whl

WORKDIR /workspace
EXPOSE 8888

ENTRYPOINT ["mercury", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
CMD []

# docker build -t mercury-dev:0.3.0 .
# docker run  -v $PWD:/workspace:rw -p 0:8888 mercury-dev:0.3.0 --timeout=30

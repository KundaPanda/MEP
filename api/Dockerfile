FROM python:3-alpine

ADD . /api
WORKDIR /api

RUN apk add --no-cache \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir -r /api/requirements.txt

RUN echo "Europe/Prague" > /etc/timezone
EXPOSE 5000

ENTRYPOINT [ "python", "-u", "/api/api.py" ]
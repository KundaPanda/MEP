FROM python:3-alpine

ADD . /api
WORKDIR /api

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && pip install --no-cache-dir -r /api/requirements.txt \
    && apk del --no-cache .build-deps

EXPOSE 5000

ENTRYPOINT [ "python", "/api/api.py" ]
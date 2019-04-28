FROM python:3-alpine

RUN pip install -r /app/requirements.txt

ADD . /api
WORKDIR /api

EXPOSE 80

ENTRYPOINT [ "python /api/api.py" ]
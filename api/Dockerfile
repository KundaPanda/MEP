FROM python:3

ADD . /api
WORKDIR /api

RUN pip install --upgrade pip
RUN pip install -r /api/requirements.txt

EXPOSE 5000

ENTRYPOINT [ "python", "/api/api.py" ]
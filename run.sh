#!/bin/bash

# api
docker build -t autisti/api-mep ./api
docker container run -d \
  --name api-mep \
  -p 80:80 \
  --restart unless-stopped \
  autisti/api-mep

# postgres
docker container run -d \
  --name postgresql-mep \
  --net container:api-mep \
  -v ${PWD}/data:/var/lib/postgresql/data
  --restart unless-stopped \
  postgres:alpine

# nginx
# docker container run -d \
#   --name nginx-mep \
#   --net skynet \
#   -p 443:433 \
#   -p 80:80 \
#   -v ${PWD}/static:/usr/share/nginx/html:ro \
#   -v ${PWD}/config/nginx.conf:/etc/nginx/nginx.conf:ro \
#   --restart unless-stopped \
#   nginx-alpine
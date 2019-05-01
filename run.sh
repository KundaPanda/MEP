#!/bin/bash

if [ ! -e ${PWD}/data ]; then
  mkdir -p ${PWD}/data
fi

docker rm -f api-mep postgresql-mep > /dev/null 2>&1

docker network create mep > /dev/null 2>&1

# postgres
docker container run -d \
  --name postgresql-mep \
  --user "$(id -u):$(id -g)" -v /etc/passwd:/etc/passwd:ro \
  -v ${PWD}/data:/var/lib/postgresql/data \
  --net mep \
  --restart unless-stopped \
  postgres:alpine

# api
docker build -t autisti/api-mep ${PWD}/api
docker container run -d \
  --name api-mep \
  --net mep \
  -p 80:5000 \
  --restart unless-stopped \
  autisti/api-mep

# nginx
# docker container run -d \
#   --name nginx-mep \
#   --net mep \
#   -p 443:433 \
#   -p 80:80 \
#   -v ${PWD}/static:/usr/share/nginx/html:ro \
#   -v ${PWD}/config/nginx.conf:/etc/nginx/nginx.conf:ro \
#   --restart unless-stopped \
#   nginx-alpine

# docker logs api-mep
# docker logs postgresql-mep
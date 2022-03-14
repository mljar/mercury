#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please specify your domain" >&2
    exit 2
fi

echo "Set domain to $1 in docker/init-letsencrypt.sh" 
sed "s/{{your_domain}}/$1/g" docker/init-letsencrypt.sh > docker/init-letsencrypt.sh

echo "Set domain to $1 in docker/nginx/pro/default.conf" 
sed "s/{{your_domain}}/$1/g" docker/nginx/pro/default.conf > docker/nginx/pro/default.conf

echo "Please run:"
echo "./docker/init-letsencrypt.sh"
echo "docker-compose -f docker-compose-pro.yml up --build -d"
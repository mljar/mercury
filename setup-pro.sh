#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please specify your domain" >&2
    exit 2
fi

echo "Set domain to $1 in docker/init-letsencrypt.sh" 
sed -i "s/{{your_domain}}/$1/g" docker/init-letsencrypt.sh

echo "Set domain to $1 in docker/nginx/pro/default.conf" 
sed -i "s/{{your_domain}}/$1/g" docker/nginx/pro/default.conf

echo "[Done] Domain set"
echo "---------------------------------------------------------"
mv docker/init-letsencrypt.sh init-letsencrypt.sh
echo "Please run following commands:"
echo "sudo ./init-letsencrypt.sh"
echo "sudo docker-compose -f docker-compose-pro.yml up --build -d"
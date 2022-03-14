#!/bin/bash
echo "Setup Mercury Pro"
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
echo "Build docker-compose:"
sudo docker-compose -f docker-compose-pro.yml build
echo "[Done] Docker-compose build"
echo "---------------------------------------------------------"
echo "Initialize SSL certificates"
sudo ./init-letsencrypt.sh
echo "[Done] SSL certificates issued"
echo "---------------------------------------------------------"
echo "Start service"
sudo docker-compose -f docker-compose-pro.yml up --build -d
echo "[Done] Mercury is running"
echo "---------------------------------------------------------"

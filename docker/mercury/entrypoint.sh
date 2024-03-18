#!/bin/sh

until cd /app/mercury
do
    echo "Waiting for server volume..."
done


until python manage.py migrate
do
    echo "Waiting for db to be ready..."
    sleep 2
done

# path with jupyter
export PATH="$HOME/.local/bin:$PATH"

echo "Docker: Add requirements for notebooks"
REQ=/app/notebooks/requirements.txt
if test -f "$REQ"; then
    pip install -r $REQ
fi

echo "Docker list files"
ls -al /app/notebooks/
ls -al /app/
echo "Docker: Add notebooks"
for filepath in /app/notebooks/*.ipynb; do
    echo "Docker: Add " $filepath
    python manage.py add $filepath
done

echo "Docker: Collect statics, for Admin Panel, DRF views"
python manage.py collectstatic --noinput

echo "Docker: Try to create super user, if doesnt exist"
python manage.py createsuperuser --noinput

echo "Docker: Start worker and beat service"
celery -A server worker --loglevel=info -P gevent --concurrency 4 -E -Q celery,ws &
celery -A server beat --loglevel=error --max-interval 60 &

echo "Docker: Start daphne server"
daphne server.asgi:application --bind 0.0.0.0 --port 9000

#gunicorn server.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4

# for debug
#python manage.py runserver 0.0.0.0:9000
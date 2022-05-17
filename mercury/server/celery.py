import os
import sys
from celery import Celery
from django.conf import settings

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CURRENT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

print("*** Start Celery ***")

print(settings.TIME_ZONE)

#  celery -A server worker --loglevel=info -P gevent --concurrency 1 -E
app = Celery("server")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.timezone = settings.TIME_ZONE

# Load task modules from all registered Django apps.
app.autodiscover_tasks()  # lambda: settings.INSTALLED_APPS)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print("setup_periodic_tasks")

    # Executes every Monday morning at 7:30 a.m.
    #sender.add_periodic_task(
    #    crontab(hour=7, minute=30, day_of_week=1),
    #    test.s('Happy Mondays!'),
    #)
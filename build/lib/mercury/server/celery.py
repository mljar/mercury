import os
import sys
from celery import Celery

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CURRENT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

#  celery -A server worker --loglevel=info -P gevent --concurrency 1 -E
app = Celery("server")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()  # lambda: settings.INSTALLED_APPS)

import json
import os
import queue
import signal
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta

import websocket
from django.utils.timezone import make_aware

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "..", "..")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
import django

django.setup()


import logging

LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    #filename="nbworker.log", filemode="w",
    format="NB %(asctime)s %(message)s",
    level=LOG_LEVEL,
)
log = logging.getLogger(__name__)


from apps.executor.nbworker.ws import WSClient


if __name__ == "__main__":
    log.info("Start nbworker __main__")
    
    print(sys.argv)
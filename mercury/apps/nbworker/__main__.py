import os
import signal
import sys
import time
import logging

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "..")
sys.path.insert(0, BACKEND_DIR)

LOG_LEVEL = (
    logging.ERROR if os.environ.get("DJANGO_LOG_LEVEL", "ERROR") == "ERROR" else logging.INFO
)

logging.basicConfig(
    # filename="nbworker.log", filemode="w",
    format="NB %(asctime)s %(message)s",
    level=LOG_LEVEL,
)
log = logging.getLogger(__name__)
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

from apps.nbworker.nb import NBWorker
from apps.nbworker.rest import RESTClient
from apps.nbworker.utils import stop_event

if len(sys.argv) != 5:
    log.error("Wrong number of input parameters")
    sys.exit(0)

notebook_id = int(sys.argv[1])
session_id = sys.argv[2]
worker_id = int(sys.argv[3])
server_url = sys.argv[4]


if os.environ.get("MERCURY_SERVER_URL") is None:
    os.environ["MERCURY_SERVER_URL"] = server_url.replace("ws://", "http://").replace(
        "wss://", "https://"
    )


def signal_handler(signal, frame):
    global stop_event
    log.info("\nBye bye!")
    stop_event.set()
    RESTClient.delete_worker_in_db(session_id, worker_id, notebook_id)
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)


RECONNECT_WAIT_TIME = 10
CONNECT_MAX_TRIES = 2


if __name__ == "__main__":
    log.info(f"Start NBWorker with arguments {sys.argv}")
    for _ in range(CONNECT_MAX_TRIES):
        nb_worker = NBWorker(
            f"{server_url}/ws/worker/{notebook_id}/{session_id}/{worker_id}/",
            notebook_id,
            session_id,
            worker_id,
        )
        time.sleep(RECONNECT_WAIT_TIME)

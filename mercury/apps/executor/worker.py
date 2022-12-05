import sys, os
import json
import websocket

from celery import shared_task
import time
import threading
import queue

import traceback
import sys

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(CURRENT_DIR, "..")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
import django

django.setup()


from apps.executor.models import Worker

print(Worker.objects.all())
from django.utils.timezone import make_aware

import sys, signal

from datetime import datetime, timedelta


print(sys.argv)
notebook_id = int(sys.argv[1])
session_id = sys.argv[2]
worker_id = int(sys.argv[3])


def signal_handler(signal, frame):
    print("\nBye bye!")
    try:
        Worker.objects.get(pk=worker_id).delete()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


q = queue.Queue()

counter = 0


def worker():
    while True:
        item = q.get()
        print(f"Working on {item}")
        time.sleep(100)
        print(f"Finished {item}")
        q.task_done()


threading.Thread(target=worker, daemon=True).start()


def on_open(ws):

    print(">> on_open")

    try:
        w = Worker.objects.get(pk=worker_id)
    except Worker.DoesNotExist as e:
        print(f"Cant find worker ({worker_id}). Quit")
        sys.exit(1)
    try:
        w.state = "Running"
        w.save()
    except Exception as e:
        print("Error when set state")
    try:
        workers = Worker.objects.filter(
            session_id=session_id, notebook__id=notebook_id, pk__lt=worker_id
        )
        workers.delete()
    except Exception as e:
        print("Error when deleting older workers.", str(e))
        print(traceback.format_exc())

    ws.send(json.dumps({"purpose": "worker-state", "state": "Running"}))


def on_message(ws, message):
    
    print(">> on_message")
    print(message)
    global counter
    print(message, counter)

    data = json.loads(message)
    print(data)

    if "purpose" in data:
        purpose = data["purpose"]
        print(purpose)
        if purpose == "worker-ping":
            try:
                w = Worker.objects.get(pk=worker_id)
                w.state = "Running"
                w.save()
            except Worker.DoesNotExist as e:
                print(f"Cant find worker ({worker_id}). Quit")
                sys.exit(1)
            ws.send(json.dumps({"purpose": "worker-state", "state": "Running"}))

    q.put(json.dumps({"counter": counter}))
    counter += 1


def on_pong(wsapp, message):
    try:
        w = Worker.objects.get(pk=worker_id)
        if w.updated_at < make_aware(datetime.now() - timedelta(minutes=1)):
            print("no ping from client, quit")
            w.delete()
            sys.exit(1)


    except Exception as e:
        print(f"on_pong error, quit")
        print(traceback.format_exc())

def on_error(ws, message):
    print("on_error", message)


def on_close(ws, close_status_code, close_msg):
    print(
        "######################################### closed ###",
        close_status_code,
        close_msg,
    )



MIN_RUN_TIME = 10  # ws should run more time than this to be considered as live
RECONNECT_WAIT_TIME = 10
CONNECT_MAX_TRIES = 2
connect_tries = 0


def worker_starting():
    workers = Worker.objects.filter(session_id=session_id)


while True:
    start_time = time.time()
    wsapp = websocket.WebSocketApp(
        f"ws://127.0.0.1:8000/ws/worker/{notebook_id}/{session_id}/{worker_id}/",
        on_message=on_message,
        on_pong=on_pong,
        on_close=on_close,
        on_open=on_open,
        on_error=on_error,
    )
    wsapp.run_forever(ping_interval=2, ping_timeout=1)
    end_time = time.time()

    # if ws running less than 10 seconds then something is wrong
    # we will try to connect again
    if end_time - start_time < MIN_RUN_TIME:
        print("Cant connect worker ...")
        connect_tries += 1
    else:
        connect_tries = 0
    if connect_tries >= CONNECT_MAX_TRIES:
        print("Stop worker")
        sys.exit(0)

    time.sleep(RECONNECT_WAIT_TIME)

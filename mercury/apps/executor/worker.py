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
BACKEND_DIR = os.path.join(CURRENT_DIR, "..")
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
import django

django.setup()

from apps.executor.models import Worker
from apps.notebooks.models import Notebook
from apps.executor.executor import Executor
from apps.executor.utils import parse_params
from execnb.nbio import read_nb, nb2dict

# input params
notebook_id = int(sys.argv[1])
session_id = sys.argv[2]
worker_id = int(sys.argv[3])

notebook = Notebook.objects.get(pk = notebook_id)
print("Loading", notebook.path)

nb = read_nb(notebook.path) 
#"/home/piotr/sandbox/mercury/mercury/demo.ipynb")
shell = Executor()

# get params
print("params from db") 
print(notebook.params)
print("***")

# first execution
shell.run_notebook(nb, export_html=False)


# get params from executed notebook
params = {}
widgets_mapping = parse_params(nb2dict(nb), params)
print(params)
print(widgets_mapping)

# compare params, and update if needed
print("TODO: update params in db if needed")


show_code = params.get("show-code", False)

print("show-code", show_code)


def delete_current_worker():
    try:
        Worker.objects.get(pk=worker_id).delete()
    except Exception:
        pass


def worker_exists_and_running(worker_id, ws):
    try:
        w = Worker.objects.get(pk=worker_id)
    except Worker.DoesNotExist as e:
        print(f"Cant find worker ({worker_id}). Quit")
        sys.exit(1)
    try:
        my_state = "Busy" if is_busy else "Running"
        w.state = my_state
        w.save()
        ws.send(json.dumps({"purpose": "worker-state", "state": my_state}))
    except Exception as e:
        print("Error when set state")



def delete_old_workers(worker_id, notebook_id, session_id):
    try:
        workers = Worker.objects.filter(
            session_id=session_id, notebook__id=notebook_id, pk__lt=worker_id
        )
        workers.delete()
    except Exception as e:
        print("Error when deleting older workers.", str(e))
        print(traceback.format_exc())


def signal_handler(signal, frame):
    print("\nBye bye!")
    delete_current_worker()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


is_busy = False
q = queue.Queue()
counter = 0


def worker():
    while True:
        item = q.get()

        json_data = json.loads(item)

        if json_data.get("purpose", "") == "run-notebook":
            is_busy = True
            wsapp.send(json.dumps({"purpose": "worker-state", "state": "Busy"}))
            body = shell.run_notebook(nb, export_html=True, full_header=False, show_code=show_code)
            is_busy = False
            wsapp.send(json.dumps({"purpose": "worker-state", "state": "Running"}))
            wsapp.send(json.dumps({"purpose": "executed-notebook", "body": body}))

        if json_data.get("purpose", "") == "clear-session":
            shell = Executor()


        q.task_done()


threading.Thread(target=worker, daemon=True).start()


def on_open(ws):
    worker_exists_and_running(worker_id, ws)
    delete_old_workers(worker_id, notebook_id, session_id)

def on_message(ws, message):

    global counter 

    data = json.loads(message)

    if "purpose" in data:
        purpose = data["purpose"]
        print(purpose)
        if purpose == "worker-ping":
            worker_exists_and_running(worker_id, ws)
        if purpose == "run-notebook":
            q.put(json.dumps({"purpose": "run-notebook"}))
        if purpose == "clear-session":
            q.put(json.dumps({"purpose": "clear-session"}))
        if purpose == "close-worker":
            delete_current_worker()
            print("no worker-ping from client, quit")
            sys.exit(1)

    counter += 1


def on_pong(wsapp, message):
    try:
        w = Worker.objects.get(pk=worker_id)
        if w.updated_at < make_aware(datetime.now() - timedelta(minutes=1)):
            w.delete()
            print("no worker-ping from client, quit")
            sys.exit(1)
    except Exception as e:
        print(f"on_pong error, quit")
        sys.exit(1)


def on_error(ws, message):
    print("on_error", message)


def on_close(ws, close_status_code, close_msg):
    print(
        "on_close",
        close_status_code,
        close_msg,
    )


MIN_RUN_TIME = 10  # ws should run more time than this to be considered as live
RECONNECT_WAIT_TIME = 10
CONNECT_MAX_TRIES = 2
connect_tries = 0


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
    wsapp.run_forever(ping_interval=5, ping_timeout=3)
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

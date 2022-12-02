import sys
import json
import websocket

from celery import shared_task

counter = 0

def on_open(wsapp):
    print(">> on_open")

def on_message(wsapp, message):
    global counter
    print(">> on_message")
    print(message, counter)

    # wsapp.send(json.dumps({
    #     "type": "chat_message",
    #     "message": "hihi"
    # }))

def on_pong(wsapp, message):
    global counter
    print("pong", counter)
    counter += 1
    #if counter > 2:
    #    sys.exit()

def on_close(wsapp, message):
    print("on_close")

wsapp = websocket.WebSocketApp(
    "ws://127.0.0.1:8000/ws/execute/example-session/", on_message=on_message,
    on_pong=on_pong, on_close=on_close, on_open=on_open
)
wsapp.run_forever(ping_interval=10, ping_timeout=5)



@shared_task(bind=True)
def task_connect(self, job_params):
    print("task connect")
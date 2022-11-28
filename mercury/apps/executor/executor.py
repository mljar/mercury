import json
import websocket

def on_open(wsapp):
    print(">> on_open")
    

def on_message(wsapp, message):
    print(">> on_message")
    print(message)

    # wsapp.send(json.dumps({
    #     "type": "chat_message",
    #     "message": "hihi"
    # }))

wsapp = websocket.WebSocketApp("ws://127.0.0.1:8000/ws/execute/example-session-id/", on_message=on_message)
wsapp.run_forever()


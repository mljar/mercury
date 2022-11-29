import { connect } from "http2";
import React, { createContext } from "react";

const WebSocketContext = createContext(undefined as any);

export { WebSocketContext };

export default function WebSocketProvider({
  children,
}: {
  children: JSX.Element;
}) {
  console.log("WebSocketProvider");
  let connection: WebSocket | undefined = undefined;
  let ws = null;

  const sendMessage = (payload: string) => {
    console.log("sendMessage", payload);

    if (connection !== undefined && connection.readyState === connection.OPEN) {
      connection.send(payload);
    }
  };

  function onOpen(event: any): void {
    console.log("connected");
  }
  function onMessage(event: any): void {
    console.log("reveived from server", event);
  }
  function onError(event: any): void {
    console.log(JSON.stringify(event.data));
  }
  function onClose(event: any): void {
    console.log(JSON.stringify(event.data));
  }
  if (connection === undefined) {
    connection = new WebSocket(
      "ws://127.0.0.1:8000/ws/execute/example-session/"
    );
    connection.onopen = onOpen;
    connection.onmessage = onMessage;
    connection.onerror = onError;
    connection.onclose = onClose;
  }

  ws = {
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

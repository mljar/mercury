import React, { createContext } from "react";
import { useDispatch } from "react-redux";
import { getSelectedNotebook } from "../components/Notebooks/notebooksSlice";
import {
  setWebSocketStatus,
  setWorkerStatus,
  WebSocketStatus,
} from "./wsSlice";

import { useSelector } from "react-redux";
import { getSessionId } from "../utils";

const WebSocketContext = createContext(undefined as any);

export { WebSocketContext };

export default function WebSocketProvider({
  children,
}: {
  children: JSX.Element;
}) {
  const dispatch = useDispatch();
  const selectedNotebook = useSelector(getSelectedNotebook);

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
    dispatch(setWebSocketStatus(WebSocketStatus.Connected));
    ping();
  }
  function onMessage(event: any): void {
    console.log("reveived from server", event);

    const response = JSON.parse(event.data);
    if ("payload" in response) {
      const { payload } = response;
      if (payload.purpose === "worker-pong") {
        dispatch(setWorkerStatus(payload.status));
      }
    }
  }
  function onError(event: any): void {
    console.log("onErrr");
    console.log(JSON.stringify(event));
    dispatch(setWebSocketStatus(WebSocketStatus.Disconnected));
  }

  function onClose(event: any): void {
    console.log("onClose");
    dispatch(setWebSocketStatus(WebSocketStatus.Disconnected));
    connection = undefined;
    setTimeout(() => connect(), 5000);
  }

  function ping(): void {
    console.log("ping");
    sendMessage(
      JSON.stringify({
        purpose: "worker-ping",
      })
    );
    if (connection !== undefined && connection.readyState === connection.OPEN) {
      setTimeout(() => ping(), 5000);
    }
  }

  function connect() {
    if (
      selectedNotebook !== undefined &&
      selectedNotebook.id !== undefined &&
      connection === undefined
    ) {
      dispatch(setWebSocketStatus(WebSocketStatus.Connecting));
      connection = new WebSocket(
        `ws://127.0.0.1:8000/ws/client/${
          selectedNotebook.id
        }/${getSessionId()}/`
      );
      connection.onopen = onOpen;
      connection.onmessage = onMessage;
      connection.onerror = onError;
      connection.onclose = onClose;
    }
  }
  connect();

  ws = {
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

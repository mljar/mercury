import React, { createContext } from "react";
import { useDispatch } from "react-redux";
import {
  getSelectedNotebookId,
  hideWidgets,
  isStaticNotebook,
  updateWidgetsParams,
  initWidgets,
} from "../components/Notebooks/notebooksSlice";
import {
  setNotebookSrc,
  setWebSocketState,
  setWorkerState,
  setWorkerId,
  WebSocketState,
  WorkerState,
} from "./wsSlice";

import { useSelector } from "react-redux";
import { getSessionId, handleDownload } from "../utils";
import { fetchExecutionHistory, setExportingToPDF } from "../tasks/tasksSlice";

const WebSocketContext = createContext(undefined as any);

export { WebSocketContext };

export default function WebSocketProvider({
  children,
}: {
  children: JSX.Element;
}) {
  console.log("WebSocketProvider");

  const dispatch = useDispatch();
  const selectedNotebookId = useSelector(getSelectedNotebookId);
  const isStatic = useSelector(isStaticNotebook);

  let connection: WebSocket | undefined = undefined;

  const sendMessage = (payload: string) => {
    if (connection !== undefined && connection.readyState === connection.OPEN) {
      connection.send(payload);
    }
  };

  function onOpen(event: any): void {
    dispatch(setWebSocketState(WebSocketState.Connected));
    ping();
  }

  function onMessage(event: any): void {
    // console.log("reveived from server", event.data);

    const response = JSON.parse(event.data);
    if ("purpose" in response) {
      if (response.purpose === "worker-state") {
        console.log("worker-state", response.state);
        dispatch(setWorkerState(response.state));
        dispatch(setWorkerId(response.workerId));
      } else if (response.purpose === "executed-notebook") {
        dispatch(setNotebookSrc(response.body));
      } else if (response.purpose === "saved-notebook") {
        if (selectedNotebookId !== undefined) {
          dispatch(fetchExecutionHistory(selectedNotebookId, false));
        }
      } else if (response.purpose === "update-widgets") {
        dispatch(updateWidgetsParams(response));
      } else if (response.purpose === "hide-widgets") {
        dispatch(hideWidgets(response));
      } else if (response.purpose === "init-widgets") {
        console.log("init-widgets")
        dispatch(initWidgets(response));
      } else if (
        response.purpose === "download-html" ||
        response.purpose === "download-pdf"
      ) {
        if (response.url && response.filename) {
          dispatch(setExportingToPDF(false));
          handleDownload(response.url, response.filename);
        }
      }
    }
  }

  function onError(event: any): void {
    dispatch(setWebSocketState(WebSocketState.Disconnected));
    dispatch(setWorkerState(WorkerState.Unknown));
  }

  function onClose(event: any): void {
    dispatch(setWebSocketState(WebSocketState.Disconnected));
    dispatch(setWorkerState(WorkerState.Unknown));
    dispatch(setWorkerId(undefined));
    connection = undefined;
    setTimeout(() => connect(), 5000);
  }

  function ping(): void {
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
      !isStatic &&
      selectedNotebookId !== undefined &&
      connection === undefined
    ) {
      connection = new WebSocket(
        `ws://127.0.0.1:8000/ws/client/${selectedNotebookId}/${getSessionId()}/`
      );
      connection.onopen = onOpen;
      connection.onmessage = onMessage;
      connection.onerror = onError;
      connection.onclose = onClose;
    }
  }
  connect();

  const ws = {
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

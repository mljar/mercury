import React, { createContext } from "react";
import { useDispatch } from "react-redux";
import {
  getSelectedNotebookId,
  hideWidgets,
  isStaticNotebook,
  updateWidgetsParams,
  initWidgets,
  fetchNotebook,
  updateTitle,
  updateShowCode,
} from "../slices/notebooksSlice";
import {
  setNotebookSrc,
  setWebSocketState,
  setWorkerState,
  setWorkerId,
  WebSocketState,
  WorkerState,
  resetTryConnectCount,
  increaseTryConnectCount,
} from "../slices/wsSlice";

import { useSelector } from "react-redux";
import { getSessionId, handleDownload } from "../utils";
import { setExportingToPDF } from "../slices/tasksSlice";
import { getSiteId } from "../slices/sitesSlice";
import { getToken } from "../slices/authSlice";

const WebSocketContext = createContext(undefined as any);

export { WebSocketContext };

let wsServer = "ws://127.0.0.1:8000";
let localServer = true;
if (process.env.REACT_APP_SERVER_WS) {
  wsServer = process.env.REACT_APP_SERVER_WS;
  localServer = false;
} else {
  if (window.location.origin === "http://localhost:3000") {
    wsServer = "ws://127.0.0.1:8000";
    localServer = true;
  } else {
    wsServer = window.location.origin
      .replace("http://", "ws://")
      .replace("https://", "wss://");
    localServer = false;
  }
}

export default function WebSocketProvider({
  children,
}: {
  children: JSX.Element;
}) {
  console.log("WebSocketProvider");

  const dispatch = useDispatch();
  const siteId = useSelector(getSiteId);
  const selectedNotebookId = useSelector(getSelectedNotebookId);
  const token = useSelector(getToken);
  const isStatic = useSelector(isStaticNotebook);
  //const tryConnectCount = useSelector(getTryConnectCount);

  let connection: WebSocket | undefined = undefined;

  const sendMessage = (payload: string) => {
    if (connection !== undefined && connection.readyState === connection.OPEN) {
      connection.send(payload);
    }
  };

  function onOpen(event: any): void {
    dispatch(resetTryConnectCount());
    sendMessage(
      JSON.stringify({
        purpose: "server-address",
        address: wsServer,
      })
    );
    dispatch(setWebSocketState(WebSocketState.Connected));
    ping();
  }

  function onMessage(event: any): void {
    // console.log("reveived from server", event.data);

    const response = JSON.parse(event.data);
    if ("purpose" in response) {
      if (response.purpose === "worker-state") {
        //console.log("worker-state", response.state);
        dispatch(setWorkerState(response.state));
        dispatch(setWorkerId(response.workerId));
      } else if (response.purpose === "executed-notebook") {
        //console.log(response?.reloadNotebook, selectedNotebookId);
        if (response?.reloadNotebook && selectedNotebookId !== undefined) {
          //console.log("reload notebook ...........................");
          dispatch(fetchNotebook(siteId, selectedNotebookId));
        }
        dispatch(setNotebookSrc(response.body));
      // } else if (response.purpose === "saved-notebook") {
      //   if (selectedNotebookId !== undefined) {
      //     dispatch(fetchExecutionHistory(selectedNotebookId, false));
      //   }
      } else if (response.purpose === "update-widgets") {
        dispatch(updateWidgetsParams(response));
      } else if (response.purpose === "hide-widgets") {
        dispatch(hideWidgets(response));
      } else if (response.purpose === "init-widgets") {
        //console.log("init-widgets");
        dispatch(initWidgets(response));
      } else if (response.purpose === "update-title") {
        dispatch(updateTitle(response.title));
      } else if (response.purpose === "update-show-code") {
        dispatch(updateShowCode(response.showCode));
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
      (localServer || !isStatic) &&
      selectedNotebookId !== undefined &&
      connection === undefined
    ) {
      dispatch(increaseTryConnectCount());
      let url = `${wsServer}/ws/client/${selectedNotebookId}/${getSessionId()}/`;
      if (token !== undefined && token !== null && token !== "") {
        url += `?token=${token}`;
      }
      connection = new WebSocket(url);
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

import React, { createContext, useEffect } from "react";
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
  setWidgetsInitialized,
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
import { getSiteId, setSiteStatus, SiteStatus } from "../slices/sitesSlice";
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

if (window.location.origin.endsWith("hf.space")) {
  wsServer = window.location.origin
    .replace("http://", "ws://")
    .replace("https://", "wss://");
  localServer = false;
}

const MAX_CONNECT_COUNT = 5;
let connectCounter = 0;
let globalConnection: WebSocket | undefined = undefined;

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

  let connection: WebSocket | undefined = undefined;
  let workerState = "Unknown" as WorkerState;

  useEffect(() => {
    connectCounter = 0;
    // returned function will be called on component unmount
    return () => {
      connectCounter = MAX_CONNECT_COUNT + 1;
      globalConnection?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        console.log("worker-state", response.state);
        workerState = response.state;

        dispatch(setWorkerState(response.state));
        dispatch(setWorkerId(response.workerId));

        if (
          workerState === WorkerState.MaxIdleTimeReached ||
          workerState === WorkerState.MaxRunTimeReached
        ) {
          connection?.close();
        }
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
        dispatch(initWidgets(response));
        dispatch(setWidgetsInitialized(true));
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
    connection = undefined;
    if (
      workerState !== WorkerState.MaxIdleTimeReached &&
      workerState !== WorkerState.MaxRunTimeReached
    ) {
      dispatch(setWorkerState(WorkerState.Unknown));
      dispatch(setWorkerId(undefined));
      if (connectCounter < MAX_CONNECT_COUNT) {
        setTimeout(() => connect(), 5000);
      }
    }
  }

  function ping(): void {
    sendMessage(
      JSON.stringify({
        purpose: "worker-ping",
      })
    );
    if (connection !== undefined && connection.readyState === connection.OPEN) {
      setTimeout(() => ping(), 10000);
    }
  }

  function connect() {
    if (
      (localServer || !isStatic) &&
      selectedNotebookId !== undefined &&
      connection === undefined &&
      workerState !== WorkerState.MaxIdleTimeReached &&
      workerState !== WorkerState.MaxRunTimeReached &&
      connectCounter < MAX_CONNECT_COUNT
    ) {
      console.log("WS connect ..." + workerState + " " + connectCounter);
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
      connectCounter += 1;

      globalConnection = connection;
      if (connectCounter >= MAX_CONNECT_COUNT) {
        dispatch(setSiteStatus(SiteStatus.NetworkError));
      }
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

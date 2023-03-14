import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getSessionId } from "../utils";
import {
  WorkerState,
  WebSocketState,
  getWebSocketState,
  getWorkerState,
  getTryConnectCount,
} from "../slices/wsSlice";
import { setSiteStatus, SiteStatus } from "../slices/sitesSlice";

export default function StatusBar() {
  const dispatch = useDispatch();
  const wsStatus = useSelector(getWebSocketState);
  const workerState = useSelector(getWorkerState);
  const tryConnectCount = useSelector(getTryConnectCount);

  useEffect(() => {
    if (tryConnectCount >= 5) {
      dispatch(setSiteStatus(SiteStatus.LostConnection));
    }
  }, [dispatch, tryConnectCount]);

  let wifiColor = "orange";
  if (wsStatus === WebSocketState.Connected) {
    wifiColor = "green";
  } else if (
    wsStatus === WebSocketState.Disconnected ||
    wsStatus === WebSocketState.Unknown
  ) {
    wifiColor = "red";
  }

  let workerColor = "orange";
  if (workerState === WorkerState.Running || workerState === WorkerState.Busy) {
    workerColor = "green";
  } else if (
    workerState === WorkerState.Missing ||
    workerState === WorkerState.Unknown
  ) {
    workerColor = "red";
  }

  return (
    <div>
      <span title={`WebSocket: ${wsStatus}`}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          fill={wifiColor}
          className="bi bi-wifi"
          viewBox="0 0 16 16"
        >
          <path d="M15.384 6.115a.485.485 0 0 0-.047-.736A12.444 12.444 0 0 0 8 3C5.259 3 2.723 3.882.663 5.379a.485.485 0 0 0-.048.736.518.518 0 0 0 .668.05A11.448 11.448 0 0 1 8 4c2.507 0 4.827.802 6.716 2.164.205.148.49.13.668-.049z" />
          <path d="M13.229 8.271a.482.482 0 0 0-.063-.745A9.455 9.455 0 0 0 8 6c-1.905 0-3.68.56-5.166 1.526a.48.48 0 0 0-.063.745.525.525 0 0 0 .652.065A8.46 8.46 0 0 1 8 7a8.46 8.46 0 0 1 4.576 1.336c.206.132.48.108.653-.065zm-2.183 2.183c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.407.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.61-.091l.016-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .707 0l.707-.707z" />
        </svg>
      </span>{" "}
      <span title={`Worker: ${workerState}\nSession Id: ${getSessionId()}`}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          fill={workerColor}
          className="bi bi-cpu"
          viewBox="0 0 16 16"
        >
          <path d="M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2A2.5 2.5 0 0 1 14 4.5h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14a2.5 2.5 0 0 1-2.5 2.5v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14A2.5 2.5 0 0 1 2 11.5H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2A2.5 2.5 0 0 1 4.5 2V.5A.5.5 0 0 1 5 0zm-.5 3A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13h7a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 11.5 3h-7zM5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5v-3zM6.5 6a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z" />
        </svg>
      </span>
      {workerState === WorkerState.Busy && (
        <span title="Worker is busy">
          {" "}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="green"
            className="bi bi-activity"
            viewBox="0 0 16 16"
          >
            <path
              fillRule="evenodd"
              d="M6 2a.5.5 0 0 1 .47.33L10 12.036l1.53-4.208A.5.5 0 0 1 12 7.5h3.5a.5.5 0 0 1 0 1h-3.15l-1.88 5.17a.5.5 0 0 1-.94 0L6 3.964 4.47 8.171A.5.5 0 0 1 4 8.5H.5a.5.5 0 0 1 0-1h3.15l1.88-5.17A.5.5 0 0 1 6 2Z"
            />
          </svg>{" "}
          Busy
        </span>
      )}
    </div>
  );
}

import React from "react";
import { getSessionId } from "../utils";
import { getSelectedNotebook } from "../components/Notebooks/notebooksSlice";
import { useSelector } from "react-redux";
import { getWebSocketStatus, getWorkerStatus } from "./wsSlice";

export default function Status() {
  const selectedNotebook = useSelector(getSelectedNotebook);
  const wsStatus = useSelector(getWebSocketStatus);
  const workerStatus = useSelector(getWorkerStatus);

  //console.log(selectedNotebook, wsStatus, workerStatus);

  if (!selectedNotebook) {
    return <p>Initialize</p>;
  }
  return (
    <div>
      <p>Notebook id: {selectedNotebook.id}</p>
      <p>WebSocket: {wsStatus}</p>
      <p>Worker: {workerStatus}</p>
      <p>Session: {getSessionId()}</p>
    </div>
  );
}

/* eslint-disable import/no-cycle */
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../store";

export enum WebSocketStatus {
  Connecting = "Connecting",
  Connected = "Connected",
  Unknown = "Unknown",
  Disconnected = "Disconnected",
}

export enum WorkerStatus {
  Unknown = "Unknown",
  Starting = "Starting",
  Running = "Running",
  Missing = "Missing",
  Busy = "Busy",
}

const initialState = {
  webSocketStatus: WebSocketStatus.Unknown,
  workerStatus: WorkerStatus.Unknown,
  notebookSrc: "",
};

const wsSlice = createSlice({
  name: "ws",
  initialState,
  reducers: {
    setWebSocketStatus(state, action: PayloadAction<WebSocketStatus>) {
      state.webSocketStatus = action.payload;
    },
    setWorkerStatus(state, action: PayloadAction<WorkerStatus>) {
      state.workerStatus = action.payload;
    },
    setNotebookSrc(state, action: PayloadAction<string>) {
      state.notebookSrc = action.payload;
    },
  },
});

export default wsSlice.reducer;

export const { setWebSocketStatus, setWorkerStatus, setNotebookSrc } =
  wsSlice.actions;

export const getWebSocketStatus = (state: RootState) =>
  state.ws.webSocketStatus;
export const getWorkerStatus = (state: RootState) => state.ws.workerStatus;
export const getNotebookSrc = (state: RootState) => state.ws.notebookSrc;

export const runNotebook = () => {
  return {
    purpose: "run-notebook",
  };
};

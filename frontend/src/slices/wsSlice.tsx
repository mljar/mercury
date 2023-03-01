/* eslint-disable import/no-cycle */
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../store";

export enum WebSocketState {
  Connecting = "Connecting",
  Connected = "Connected",
  Unknown = "Unknown",
  Disconnected = "Disconnected",
}

export enum WorkerState {
  Unknown = "Unknown",
  Starting = "Starting",
  Running = "Running",
  Missing = "Missing",
  Busy = "Busy",
  Queued = "Queued",
}

const initialState = {
  webSocketState: WebSocketState.Unknown,
  workerState: WorkerState.Unknown,
  workerId: undefined as undefined | number,
  notebookSrc: "",
};

const wsSlice = createSlice({
  name: "ws",
  initialState,
  reducers: {
    setWebSocketState(state, action: PayloadAction<WebSocketState>) {
      state.webSocketState = action.payload;
    },
    setWorkerState(state, action: PayloadAction<WorkerState>) {
      state.workerState = action.payload;
    },
    setWorkerId(state, action: PayloadAction<undefined | number>) {
      state.workerId = action.payload;
    },
    setNotebookSrc(state, action: PayloadAction<string>) {
      state.notebookSrc = action.payload;
    },
  },
});

export default wsSlice.reducer;

export const {
  setWebSocketState,
  setWorkerState,
  setWorkerId,
  setNotebookSrc,
} = wsSlice.actions;

export const getWebSocketState = (state: RootState) => state.ws.webSocketState;
export const getWorkerState = (state: RootState) => state.ws.workerState;
export const getWorkerId = (state: RootState) => state.ws.workerId;
export const getNotebookSrc = (state: RootState) => state.ws.notebookSrc;

export const runNotebook = (widgets_params: string) => {
  return {
    purpose: "run-notebook",
    widgets: widgets_params,
  };
};

export const saveNotebook = () => {
  return {
    purpose: "save-notebook",
  };
};

export const displayNotebook = (taskId: number) => {
  return {
    purpose: "display-notebook",
    taskId,
  };
};

export const downloadHTML = () => {
  return {
    purpose: "download-html",
  };
};

export const downloadPDF = () => {
  return {
    purpose: "download-pdf",
  };
};

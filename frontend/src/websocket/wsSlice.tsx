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
}

const initialState = {
  WebSocketState: WebSocketState.Unknown,
  WorkerState: WorkerState.Unknown,
  notebookSrc: "",
};

const wsSlice = createSlice({
  name: "ws",
  initialState,
  reducers: {
    setWebSocketState(state, action: PayloadAction<WebSocketState>) {
      state.WebSocketState = action.payload;
    },
    setWorkerState(state, action: PayloadAction<WorkerState>) {
      state.WorkerState = action.payload;
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
  setNotebookSrc,
} = wsSlice.actions;

export const getWebSocketState = (state: RootState) =>
  state.ws.WebSocketState;
export const getWorkerState = (state: RootState) => state.ws.WorkerState;
export const getNotebookSrc = (state: RootState) => state.ws.notebookSrc;

export const runNotebook = (widgets_params: string) => {
  
  return {
    purpose: "run-notebook",
    widgets: widgets_params,
  };
};

/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';

import { RootState } from '../store';
import { getSessionId } from '../utils';


const initialState = {
  view: "app",
  files: [] as string[],
  filesState: "unknown",
  showSideBar: true,
  storageType: "media",
  showShareDialog: false,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setView(state, action: PayloadAction<string>) {
      state.view = action.payload;
    },
    setFilesState(state, action: PayloadAction<string>) {
      state.filesState = action.payload;
    },
    setFiles(state, action: PayloadAction<string[]>) {
      state.files = action.payload;
    },
    setShowSideBar(state, action: PayloadAction<boolean>) {
      state.showSideBar = action.payload;
    },
    toggleShowSideBar(state) {
      state.showSideBar = !state.showSideBar;
    },
    setStorageType(state, action: PayloadAction<string>) {
      state.storageType = action.payload;
    },
    setShowShareDialog(state, action: PayloadAction<boolean>) {
      state.showShareDialog = action.payload;
    }
  },
});

export default appSlice.reducer;

export const {
  setView,
  setFilesState,
  setFiles,
  setShowSideBar,
  toggleShowSideBar,
  setStorageType,
  setShowShareDialog,
} = appSlice.actions;


export const getView = (state: RootState) => state.app.view;
export const getOutputFilesState = (state: RootState) => state.app.filesState;
export const getOutputFiles = (state: RootState) => state.app.files;
export const getShowSideBar = (state: RootState) => state.app.showSideBar;
export const getStorageType = (state: RootState) => state.app.storageType;
export const getShowShareDialog = (state: RootState) => state.app.showShareDialog;


export const fetchOutputFiles =
  (taskId: number) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        dispatch(setFilesState("loading"))
        dispatch(setFiles([]));
        const sessionId = getSessionId();
        const url = `/api/v1/output_files/${sessionId}/${taskId}/`;
        const { data } = await axios.get(url);
        dispatch(setFiles(data));
        dispatch(setFilesState("loaded"))
      } catch (error) {
        dispatch(setFilesState("error"))
        console.error(`Problem during loading output files. ${error}`);
      }

    };

export const fetchWorkerOutputFiles =
  (workerId: number, notebookId: number) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        dispatch(setFilesState("loading"))
        dispatch(setFiles([]));
        const sessionId = getSessionId();
        const url = `/api/v1/worker-output-files/${sessionId}/${workerId}/${notebookId}/`;
        const { data } = await axios.get(url);
        dispatch(setFiles(data));
        dispatch(setFilesState("loaded"))
      } catch (error) {
        dispatch(setFilesState("error"))
        console.error(`Problem during loading worker output files. ${error}`);
      }

    };


export const fetchStorageType =
  () =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        const url = `/api/v1/storage-type`;
        const { data } = await axios.get(url);
        dispatch(setStorageType(data.storage_type));

      } catch (error) {
        console.error(`Get storage type error. ${error}`);
      }

    };

export const userFileUploaded =
  (siteId: number, sessionId: string, filename: string) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        const data = { site_id: siteId, session_id: sessionId, filename }
        const url = `/api/v1/nb-file-uploaded`;
        await axios.post(url, data);
      } catch (error) {
        console.error(`Problem with file upload. ${error}`);
      }
    };


export const deleteUserFileUploaded =
  (siteId: number, sessionId: string, filename: string) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        const data = { site_id: siteId, session_id: sessionId, filename }
        const url = `/api/v1/nb-delete-file`;
        await axios.post(url, data);
      } catch (error) {
        console.error(`Problem with file upload. ${error}`);
      }
    };
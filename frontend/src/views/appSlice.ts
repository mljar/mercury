/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';

import { RootState } from '../store';


const initialState = {
  view: "app",
  files: [] as string[],
  filesState: "loading",
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
    setFiles(state, action: PayloadAction<string []>) {
      state.files = action.payload;
    }
  },
});

export default appSlice.reducer;

export const {
  setView,
  setFilesState,
  setFiles,
} = appSlice.actions;

export const getView = (state: RootState) => state.app.view;


export const fetchOutputFiles =
  (taskId: number) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        dispatch(setFilesState("loading"))
        dispatch(setFiles([]));
        const url = `/api/v1/output_files/${taskId}`;
        const { data } = await axios.get(url);
        dispatch(setFiles(data));
        dispatch(setFilesState("loaded"))
      } catch (error) {
        dispatch(setFilesState("error"))
        console.error(`Problem during loading output files. ${error}`);
      }

    };

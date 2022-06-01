/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';

import { RootState } from '../../store';
import { setShowSideBar } from '../../views/appSlice';
import { IWidget } from '../Widgets/Types';
import { getWindowDimensions } from '../WindowDimensions';

export interface INotebookParams {
  title: string | null;
  description: string | null;
  date: string | null;
  author: string | null;
  params: IWidget[];
}

export interface INotebook {
  id: number;
  created_at: Date;
  file_updated_at: Date;
  title: string;
  slug: string;
  path: string;
  share: string;
  params: INotebookParams;
  state: string;
  default_view_path: string;
  output: string;
  format: string;
  slidesHash: string;
  schedule: string;
  errors: string;
}

const initialState = {
  notebooks: [] as INotebook[],
  loadingState: "loading",
  selectedNotebook: {} as INotebook,
  loadingStateSelected: "loading",
  watchModeCounter: 0,
  slidesHash: "",
};

const notebooksSlice = createSlice({
  name: 'notebooks',
  initialState,
  reducers: {
    setNotebooks(state, action: PayloadAction<INotebook[]>) {
      state.notebooks = action.payload;
    },
    setLoadingState(state, action: PayloadAction<string>) {
      state.loadingState = action.payload;
    },
    setSelectedNotebook(state, action: PayloadAction<INotebook>) {

      if (action.payload.state.startsWith("WATCH") && state.selectedNotebook.file_updated_at === action.payload.file_updated_at) {
        // console.log("skip notebook update")
      } else {
        state.selectedNotebook = action.payload;
      }
      if (action.payload.state.startsWith("WATCH")) {
        state.watchModeCounter += 1;
      }
    },
    setLoadingStateSelected(state, action: PayloadAction<string>) {
      state.loadingStateSelected = action.payload;
    },
    setSlidesHash(state, action: PayloadAction<string>) {
      state.slidesHash = action.payload;
    },
  },
});

export default notebooksSlice.reducer;

export const {
  setNotebooks,
  setLoadingState,
  setSelectedNotebook,
  setLoadingStateSelected,
  setSlidesHash,
} = notebooksSlice.actions;

export const getNotebooks = (state: RootState) => state.notebooks.notebooks;
export const getLoadingState = (state: RootState) => state.notebooks.loadingState;
export const getSelectedNotebook = (state: RootState) => state.notebooks.selectedNotebook;
export const getLoadingStateSelected = (state: RootState) => state.notebooks.loadingStateSelected;
export const getWatchModeCounter = (state: RootState) => state.notebooks.watchModeCounter;
export const getSlidesHash = (state: RootState) => state.notebooks.slidesHash;

export const fetchNotebooks =
  () =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        dispatch(setSlidesHash(""));
        dispatch(setLoadingState("loading"))
        const url = '/api/v1/notebooks/';
        const { data } = await axios.get(url);
        const parsedNotebooks = data.map((notebook: any) => {
          const parsedParams = JSON.parse(notebook.params)

          return {
            ...notebook,
            params: parsedParams as INotebookParams,
          }
        })
        dispatch(setNotebooks(parsedNotebooks));
        dispatch(setLoadingState("loaded"))
      } catch (error) {
        dispatch(setLoadingState("error"))
        console.error(`Problem during loading recent notebooks. ${error}`);
      }

    };


export const fetchNotebook =
  (id: number, silent = false) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        if(!silent) {
          dispatch(setSlidesHash(""));
        }

        const { width } = getWindowDimensions();
        dispatch(setShowSideBar(width > 992));

        if (!silent) {
          dispatch(setLoadingStateSelected("loading"))
        }
        const url = `/api/v1/notebooks/${id}/`;
        const { data } = await axios.get(url);
        const parsedParams = JSON.parse(data.params)
        dispatch(setSelectedNotebook(
          {
            ...data,
            params: parsedParams as INotebookParams,
          }
        ));
        if (!silent) {
          dispatch(setLoadingStateSelected("loaded"))
        }
      } catch (error) {
        if (!silent) {
          dispatch(setLoadingStateSelected("error"))
        }
        console.error(`Problem during loading selected notebook (${id}). ${error}`);
      }
    };


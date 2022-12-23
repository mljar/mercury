/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';
import { createEmitAndSemanticDiagnosticsBuilderProgram } from 'typescript';

import { RootState } from '../../store';
import { clearExecutionHistory } from '../../tasks/tasksSlice';
import { setShowSideBar } from '../../views/appSlice';
import { IWidget, isSelectWidget, isSliderWidget, isTextWidget, isRangeWidget } from '../Widgets/Types';
//import { setWidgetValue } from '../Widgets/widgetsSlice';
import { getWindowDimensions } from '../WindowDimensions';

export interface INotebookParams {
  title: string | null;
  description: string | null;
  date: string | null;
  author: string | null;
  'show-code': boolean | null;
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

type WidgetValueType = string | boolean | number | [number, number] | string[] | null | undefined | unknown;

const initialState = {
  notebooks: [] as INotebook[],
  loadingState: "loading",
  selectedNotebook: {} as INotebook,
  selectedNotebookId: undefined as undefined | Number,
  loadingStateSelected: "loading",
  watchModeCounter: 0,
  slidesHash: "",
  widgets: {} as Record<string, WidgetValueType>
};

const notebooksSlice = createSlice({
  name: 'notebooks',
  initialState,
  reducers: {
    setWidgetValue(state, action: PayloadAction<{ key: string, value: WidgetValueType }>) {
      const { key, value } = action.payload;
      console.log("set widget value", key, value)
      state.widgets[key] = value;
    },
    clearWidgets(state) {
      state.widgets = {};
    },
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
        state.selectedNotebookId = state.selectedNotebook.id;
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
    updateWidgetsParams(state, action: PayloadAction<any>) {
      console.log("udapte widgets params");
      console.log(action.payload);

      const { widgetKey } = action.payload;

      let updated = false;

      for (let key of Object.keys(state.selectedNotebook.params.params)) {
        console.log(key);
        if (key === widgetKey) {
          console.log("** match **")

          let widget = { ...state.selectedNotebook.params.params[widgetKey] };

          if (isRangeWidget(widget)) {
            if (widget.min !== action.payload.min) {
              widget.min = action.payload.min;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.max !== action.payload.max) {
              widget.max = action.payload.max;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.step !== action.payload.step) {
              widget.step = action.payload.step;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          } else if (isTextWidget(widget)) {
            if (widget.rows !== action.payload.rows) {
              widget.rows = action.payload.rows;
              updated = true;
            }
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          } else if (isSliderWidget(widget)) {
            if (widget.min !== action.payload.min) {
              widget.min = action.payload.min;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.max !== action.payload.max) {
              widget.max = action.payload.max;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.step !== action.payload.step) {
              widget.step = action.payload.step;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          } else if (isSelectWidget(widget)) {
            if (widget.choices.toString() !== action.payload.choices.toString()) {
              widget.choices = action.payload.choices;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          }


          if (updated) {
            state.selectedNotebook.params.params[widgetKey] = widget;
          }
        }
      }
    }
  },

});

export default notebooksSlice.reducer;

export const {
  setNotebooks,
  setLoadingState,
  setSelectedNotebook,
  setLoadingStateSelected,
  setSlidesHash,
  updateWidgetsParams,
  setWidgetValue,
  clearWidgets,
} = notebooksSlice.actions;

export const getNotebooks = (state: RootState) => state.notebooks.notebooks;
export const getLoadingState = (state: RootState) => state.notebooks.loadingState;
export const getSelectedNotebook = (state: RootState) => state.notebooks.selectedNotebook;
export const getSelectedNotebookId = (state: RootState) => state.notebooks.selectedNotebookId;
export const getLoadingStateSelected = (state: RootState) => state.notebooks.loadingStateSelected;
export const getWatchModeCounter = (state: RootState) => state.notebooks.watchModeCounter;
export const getSlidesHash = (state: RootState) => state.notebooks.slidesHash;

export const getWidgetsValues = (state: RootState) => state.notebooks.widgets;

export const fetchNotebooks =
  () =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        dispatch(setSlidesHash(""));
        dispatch(setLoadingState("loading"));
        dispatch(clearExecutionHistory());
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
        if (!silent) {
          dispatch(setSlidesHash(""));
          dispatch(clearExecutionHistory());
        }

        const { width } = getWindowDimensions();
        dispatch(setShowSideBar(width > 992));

        if (!silent) {
          dispatch(setLoadingStateSelected("loading"));
        }
        const url = `/api/v1/notebooks/${id}/`;
        const { data } = await axios.get(url);
        const parsedParams = JSON.parse(data.params);
        dispatch(setSelectedNotebook(
          {
            ...data,
            params: parsedParams as INotebookParams,
          }
        ));
        if (!silent) {
          dispatch(setLoadingStateSelected("loaded"));
        }
      } catch (error) {
        if (!silent) {
          dispatch(setLoadingStateSelected("error"));
        }
        console.error(`Problem during loading selected notebook (${id}). ${error}`);
      }
    };


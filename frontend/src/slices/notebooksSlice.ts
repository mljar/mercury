/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from "@reduxjs/toolkit";
import axios from "axios";

import { RootState } from "../store";
import { clearExecutionHistory } from "./tasksSlice";
import { setShowSideBar } from "./appSlice";
import {
  IWidget,
  isSelectWidget,
  isSliderWidget,
  isTextWidget,
  isRangeWidget,
  isCheckboxWidget,
  isNumericWidget,
  isMarkdownWidget,
  isButtonWidget,
} from "../widgets/Types";
import { getWindowDimensions } from "../components/WindowDimensions";

export const RUN_DELAY = 600; // ms
export const RUN_DELAY_FAST = 100; // ms

export interface INotebookParams {
  title: string | null;
  description: string | null;
  date: string | null;
  author: string | null;
  "show-code": boolean | null;
  params: Record<string, IWidget>; //IWidget[];
  version: string;
  continuous_update: boolean;
  static_notebook: boolean;
  show_sidebar: boolean;
  full_screen: boolean;
  allow_download: boolean;
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

type WidgetValueType =
  | string
  | boolean
  | number
  | [number, number]
  | string[]
  | null
  | undefined
  | unknown;

const initialState = {
  notebooks: [] as INotebook[],
  loadingState: "loading",
  selectedNotebook: {} as INotebook,
  selectedNotebookId: undefined as undefined | number,
  loadingStateSelected: "loading",
  watchModeCounter: 0,
  slidesHash: "",
  widgets: {} as Record<string, WidgetValueType>,
  nbIframes: {} as Record<string, string>, // slug -> signed URL
};

const notebooksSlice = createSlice({
  name: "notebooks",
  initialState,
  reducers: {
    setWidgetValue(
      state,
      action: PayloadAction<{ key: string; value: WidgetValueType }>
    ) {
      const { key, value } = action.payload;
      state.widgets[key] = value;
      //console.log({ key, value });
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
      if (
        action.payload.state.startsWith("WATCH") &&
        state.selectedNotebook.file_updated_at ===
        action.payload.file_updated_at
      ) {
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
      const { widgetKey } = action.payload;

      let updated = false;

      let noMatch = true;

      for (let key of Object.keys(state.selectedNotebook.params.params)) {
        if (key === widgetKey) {
          noMatch = false;
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
            if (
              widget.choices.toString() !== action.payload.choices.toString()
            ) {
              widget.choices = action.payload.choices;
              state.widgets[key] = action.payload.value;
              updated = true;
            }
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          } else if (isCheckboxWidget(widget)) {
            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
          } else if (isNumericWidget(widget)) {
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
          } else if (isMarkdownWidget(widget)) {
            if (widget.value !== action.payload.value) {
              widget.value = action.payload.value;
              updated = true;
            }
          } else if (isButtonWidget(widget)) {
            state.widgets[key] = action.payload.value;

            if (widget.label !== action.payload.label) {
              widget.label = action.payload.label;
              updated = true;
            }
            if (widget.style !== action.payload.style) {
              widget.style = action.payload.style;
              updated = true;
            }
          }

          if (updated) {
            state.selectedNotebook.params.params[widgetKey] = widget;
          }
        }
      }
      if (noMatch) {
        state.selectedNotebook.params.params[widgetKey] = action.payload;
      }
    },
    hideWidgets(state, action: PayloadAction<any>) {
      const { keys } = action.payload;
      for (let key of keys) {
        if (key in state.selectedNotebook.params.params) {
          delete state.selectedNotebook.params.params[key];
        }
      }
    },
    initWidgets(state, action: PayloadAction<any>) {
      const { widgets } = action.payload;
      state.selectedNotebook.params.params = {}
      state.widgets = {}
      for (let widget of widgets) {
        // console.log(widget);
        state.selectedNotebook.params.params[widget.widgetKey] = widget;
        state.widgets[widget.widgetKey] = widget.value;

      }
    },
    updateTitle(state, action: PayloadAction<string>) {
      state.selectedNotebook.title = action.payload;
    },
    updateShowCode(state, action: PayloadAction<boolean>) {
      state.selectedNotebook.params["show-code"] = action.payload;
    },
    setNbIframes(state, action: PayloadAction<Record<string, string>>) {
      state.nbIframes = action.payload;
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
  hideWidgets,
  setWidgetValue,
  clearWidgets,
  initWidgets,
  updateTitle,
  updateShowCode,
  setNbIframes
} = notebooksSlice.actions;

export const getNotebooks = (state: RootState) => state.notebooks.notebooks;
export const getLoadingState = (state: RootState) =>
  state.notebooks.loadingState;
export const getSelectedNotebook = (state: RootState) =>
  state.notebooks.selectedNotebook;
export const getSelectedNotebookId = (state: RootState) =>
  state.notebooks.selectedNotebookId;
export const isStaticNotebook = (state: RootState) => {
  let st = state.notebooks.selectedNotebook?.params?.static_notebook;
  if (st === undefined) {
    return false;
  }
  return st;
};
export const getLoadingStateSelected = (state: RootState) =>
  state.notebooks.loadingStateSelected;
export const getWatchModeCounter = (state: RootState) =>
  state.notebooks.watchModeCounter;
export const getSlidesHash = (state: RootState) => state.notebooks.slidesHash;

export const getWidgetsValues = (state: RootState) => state.notebooks.widgets;
export const getNbIframes = (state: RootState) => state.notebooks.nbIframes;


export const fetchNbIframes = (siteId: number) => async (dispatch: Dispatch<AnyAction>) => {
  try {
    const url = `/api/v1/${siteId}/nb-iframes/`;
    const { data } = await axios.get(url);
    dispatch(setNbIframes(data));
  } catch (error) {
    console.error(`Problem during loading notebooks iframes. ${error}`);
  }
};


export const fetchNotebooks = (siteId: number) => async (dispatch: Dispatch<AnyAction>) => {
  try {
    dispatch(setSlidesHash(""));
    dispatch(setLoadingState("loading"));
    dispatch(clearExecutionHistory());
    const url = `/api/v1/${siteId}/notebooks/`;
    const { data } = await axios.get(url);
    const parsedNotebooks = data.map((notebook: any) => {
      const parsedParams = JSON.parse(notebook.params);

      return {
        ...notebook,
        params: parsedParams as INotebookParams,
      };
    });
    dispatch(setNotebooks(parsedNotebooks));
    dispatch(setLoadingState("loaded"));
  } catch (error) {
    dispatch(setLoadingState("error"));
    console.error(`Problem during loading recent notebooks. ${error}`);
  }
};

export const fetchNotebook =
  (siteId: number, id: number, silent = false) =>
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
        const url = `/api/v1/${siteId}/notebooks/${id}/`;
        const { data } = await axios.get(url);
        const parsedParams = JSON.parse(data.params) as INotebookParams;
        dispatch(
          setSelectedNotebook({
            ...data,
            params: parsedParams,
          })
        );
        if (!silent) {
          dispatch(setLoadingStateSelected("loaded"));
        }
        if (parsedParams?.show_sidebar !== null && parsedParams?.show_sidebar !== undefined) {
          dispatch(setShowSideBar(parsedParams?.show_sidebar));
        }
      } catch (error) {
        if (!silent) {
          dispatch(setLoadingStateSelected("error"));
        }
        console.error(
          `Problem during loading selected notebook (${id}). ${error}`
        );
      }
    };

export const fetchNotebookWithSlug =
  (siteId: number, slug: string, silent = false) =>
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
        const url = `/api/v1/${siteId}/getnb/${slug}/`;
        const { data } = await axios.get(url);
        const parsedParams = JSON.parse(data.params) as INotebookParams;
        dispatch(
          setSelectedNotebook({
            ...data,
            params: parsedParams,
          })
        );
        if (!silent) {
          dispatch(setLoadingStateSelected("loaded"));
        }
        if (parsedParams?.show_sidebar !== null && parsedParams?.show_sidebar !== undefined) {
          dispatch(setShowSideBar(parsedParams?.show_sidebar));
        }
      } catch (error) {
        if (!silent) {
          dispatch(setLoadingStateSelected("error"));
        }
        console.error(
          `Problem during loading selected notebook (${slug}). ${error}`
        );
      }
    };

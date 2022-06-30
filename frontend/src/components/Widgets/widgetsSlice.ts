/* eslint-disable import/no-cycle */
import {
    createSlice,
    PayloadAction,
} from '@reduxjs/toolkit';

import { RootState } from '../../store';

const initialState = {
    widgets: {} as Record<string, string | boolean | number | [number, number] | string[] | null | undefined | unknown>
};

const widgetsSlice = createSlice({
    name: 'widgets',
    initialState,
    reducers: {
        setWidgetValue(state, action: PayloadAction<{ key: string, value: string | boolean | number | [number, number] | string[] | null | undefined | unknown }>) {
            const { key, value } = action.payload;
            state.widgets[key] = value;
        },
        clearWidgets(state) {
            state.widgets = {};
        }
    },
});

export default widgetsSlice.reducer;

export const {
    setWidgetValue,
    clearWidgets,
} = widgetsSlice.actions;

export const getWidgetsValues = (state: RootState) => state.widgets.widgets;
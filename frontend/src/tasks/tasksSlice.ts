/* eslint-disable import/no-cycle */
import {
    createSlice,
    AnyAction,
    Dispatch,
    PayloadAction,
} from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';

import { getSessionId } from '../utils';

export interface ITask {
    id: number;
    task_id: string;
    session_id: string;
    created_at: Date;
    state: "CREATED" | "RECEIVED" | "DONE" | "ERROR";
    params: string;
    result: string;
}

const initialState = {
    currentTask: {} as ITask,
};

const tasksSlice = createSlice({
    name: 'tasks',
    initialState,
    reducers: {
        setCurrentTask(state, action: PayloadAction<ITask>) {
            state.currentTask = action.payload;
        },
    },
});

export default tasksSlice.reducer;

export const {
    setCurrentTask
} = tasksSlice.actions;

export const getCurrentTask = (state: RootState) => state.tasks.currentTask;


export const fetchCurrentTask =
    (notebookId: Number) =>
        async (dispatch: Dispatch<AnyAction>) => {

            const sessionId = getSessionId();

            try {
                const url = `/api/v1/latest_task/${notebookId}/${sessionId}`;
                const { data } = await axios.get(url);
                dispatch(setCurrentTask(data))

            } catch (error) {
                // console.clear();
                dispatch(setCurrentTask({} as ITask));
            }

        };


export const executeNotebook =
    (notebookId: Number) =>
        async (dispatch: Dispatch<AnyAction>, getState: () => any) => {
            const { widgets } = getState().widgets;
            const sessionId = getSessionId();

            console.log("run notebook");


            try {
                const task = {
                    session_id: sessionId,
                    params: JSON.stringify(widgets),
                }
                console.log(task)
                const url = `/api/v1/execute/${notebookId}`;
                const { data } = await axios.post(url, task);
                console.log(data)
                dispatch(setCurrentTask(data))

            } catch (error) {
                console.error(`Problem during notebook execution. ${error}`);
            }

        };


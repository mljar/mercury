/* eslint-disable import/no-cycle */
import {
    createSlice,
    AnyAction,
    Dispatch,
    PayloadAction,
} from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';
import { toast } from "react-toastify";
import { getSessionId, handleDownload } from '../utils';
import { setSlidesHash } from './notebooksSlice';

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
    historicTask: {} as ITask,
    showCurrent: true,
    previousTask: {} as ITask,
    exportingToPDF: false,
    exportToPDFJobId: '',
    exportToPDFCounter: 0,
    executionHistory: [] as ITask[],
};

const tasksSlice = createSlice({
    name: 'tasks',
    initialState,
    reducers: {
        setShowCurrent(state, action: PayloadAction<boolean>) {
            state.showCurrent = action.payload;
        },
        setCurrentTask(state, action: PayloadAction<ITask>) {
            state.currentTask = action.payload;
        },
        setHistoricTask(state, action: PayloadAction<ITask>) {
            state.historicTask = action.payload;
        },
        setPreviousTask(state, action: PayloadAction<ITask>) {
            state.previousTask = action.payload;
        },
        copyCurrentToPreviousTask(state) {
            state.previousTask = state.currentTask;
        },
        setExportingToPDF(state, action: PayloadAction<boolean>) {
            state.exportingToPDF = action.payload;
        },
        setExportToPDFJobId(state, action: PayloadAction<string>) {
            state.exportToPDFJobId = action.payload;
        },
        resetExportToPDFCounter(state) {
            state.exportToPDFCounter = 0;
        },
        increaseExportToPDFCounter(state) {
            state.exportToPDFCounter += 1;
        },
        stopPDFExport(state) {
            state.exportingToPDF = false;
            state.exportToPDFJobId = "";
            state.exportToPDFCounter = 0;
        },
        setExecutionHistory(state, action: PayloadAction<ITask[]>) {
            state.executionHistory = action.payload;
        },
        clearExecutionHistory(state) {
            state.executionHistory = [];
        }
    },
});

export default tasksSlice.reducer;

export const {
    setShowCurrent,
    setCurrentTask,
    setHistoricTask,
    setPreviousTask,
    copyCurrentToPreviousTask,
    setExportingToPDF,
    setExportToPDFJobId,
    resetExportToPDFCounter,
    increaseExportToPDFCounter,
    stopPDFExport,
    setExecutionHistory,
    clearExecutionHistory,
} = tasksSlice.actions;

export const getShowCurrent = (state: RootState) => state.tasks.showCurrent;
export const getCurrentTask = (state: RootState) => state.tasks.currentTask;
export const getHistoricTask = (state: RootState) => state.tasks.historicTask;
export const getPreviousTask = (state: RootState) => state.tasks.previousTask;
export const getExportingToPDF = (state: RootState) => state.tasks.exportingToPDF;
export const getExportToPDFJobId = (state: RootState) => state.tasks.exportToPDFJobId;
export const getExportToPDFCounter = (state: RootState) => state.tasks.exportToPDFCounter;
export const getExecutionHistory = (state: RootState) => state.tasks.executionHistory;

export const fetchCurrentTask =
    (notebookId: Number) =>
        async (dispatch: Dispatch<AnyAction>) => {

            const sessionId = getSessionId();

            try {
                const url = `/api/v1/latest_task/${notebookId}/${sessionId}/`;
                const { data } = await axios.get(url);
                dispatch(setCurrentTask(data))

            } catch (error) {
                // console.clear();
                dispatch(setCurrentTask({} as ITask));
            }

        };

export const scrapeSlidesHash = () => {
    try {
        const iframeElement = (document.getElementById("main-iframe") as HTMLIFrameElement);
        const hash = iframeElement?.contentWindow?.location?.hash;
        if (hash) {
            return hash;
        }
    } catch (error) { }
    return "";
}


export const executeNotebook =
    (notebookId: Number) =>
        async (dispatch: Dispatch<AnyAction>, getState: () => any) => {
            const { widgets } = getState().widgets;
            const sessionId = getSessionId();

            const slidesHash = scrapeSlidesHash();
            dispatch(setSlidesHash(slidesHash));

            try {
                const task = {
                    session_id: sessionId,
                    params: JSON.stringify(widgets),
                }
                const url = `/api/v1/execute/${notebookId}/`;
                const { data } = await axios.post(url, task);
                dispatch(setCurrentTask(data))

            } catch (error) {
                console.error(`Problem during notebook execution. ${error}`);
            }

        };


export const clearTasks =
    (notebookId: Number) =>
        async (dispatch: Dispatch<AnyAction>) => {
            try {
                const sessionId = getSessionId();
                const url = `/api/v1/clear_tasks/${notebookId}/${sessionId}/`;
                await axios.post(url);
                dispatch(setCurrentTask({} as ITask));
                dispatch(setHistoricTask({} as ITask));
                dispatch(setPreviousTask({} as ITask));
                dispatch(setExecutionHistory([]));
                toast.success("All previous tasks deleted. The default view of the app is displayed.")
            } catch (error) {
                toast.error(`Trying to clear previous tasks. The error occured. ${error}`)
            }
        };


export const exportToPDF =
    (notebookId: Number, notebookPath: String) =>
        async (dispatch: Dispatch<AnyAction>) => {
            try {
                dispatch(setExportingToPDF(true));
                dispatch(resetExportToPDFCounter());
                dispatch(setExportToPDFJobId(""));

                const sessionId = getSessionId();
                const url = `/api/v1/export_pdf/`;
                // convert from JS camel case to Python undescore variables
                const params = {
                    session_id: sessionId,
                    notebook_id: notebookId,
                    notebook_path: notebookPath,
                }
                const { data } = await axios.post(url, params);
                dispatch(setExportToPDFJobId(data.job_id))
            } catch (error) {
                toast.error(`The error occured during PDF export. ${error}`);
                dispatch(stopPDFExport());
            }
        };

export const getPDF =
    (jobId: String) =>
        async (dispatch: Dispatch<AnyAction>) => {
            try {
                const url = `/api/v1/get_pdf/${jobId}/`;
                const { data } = await axios.get(url);
                if (data.ready) {
                    dispatch(stopPDFExport());
                    if (data.error !== "") {
                        toast.error(data.error);
                    } else {
                        handleDownload(
                            `${axios.defaults.baseURL}${data.url}`,
                            `${data.title}`
                        )
                    }
                } else {
                    dispatch(increaseExportToPDFCounter());
                }
            } catch (error) {
                toast.error(`The error occured during PDF export. ${error}`);
                dispatch(stopPDFExport());
            }
        };



export const fetchExecutionHistory =
    (notebookId: Number, clearPreviousHistory = true) =>
        async (dispatch: Dispatch<AnyAction>) => {

            dispatch(setHistoricTask({} as ITask));
            if (clearPreviousHistory) {
                dispatch(clearExecutionHistory());
            }

            const sessionId = getSessionId();

            try {
                const url = `/api/v1/execution_history/${notebookId}/${sessionId}/`;
                const { data } = await axios.get(url);
                dispatch(setExecutionHistory(data))
            } catch (error) {
                dispatch(clearExecutionHistory());
            }

        };

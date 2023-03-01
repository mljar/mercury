/* eslint-disable import/no-cycle */
import { combineReducers } from 'redux';
import { History } from 'history';
import notebooksReducer from './slices/notebooksSlice';
import tasksReducer from './slices/tasksSlice';
import versionReducer from './slices/versionSlice';
import appReducer from './slices/appSlice';
import authReducer from "./slices/authSlice";
import wsReducer from "./slices/wsSlice";
import sitesReducer from "./slices/sitesSlice";

export default function createRootReducer(history: History) {
    return combineReducers({
        notebooks: notebooksReducer,
        tasks: tasksReducer,
        // widgets: widgetsReducer,
        version: versionReducer,
        app: appReducer,
        auth: authReducer,
        ws: wsReducer,
        sites: sitesReducer,
    });
}

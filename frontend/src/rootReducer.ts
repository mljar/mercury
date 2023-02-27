/* eslint-disable import/no-cycle */
import { combineReducers } from 'redux';
import { History } from 'history';
import notebooksReducer from './components/Notebooks/notebooksSlice';
import tasksReducer from './tasks/tasksSlice';
//import widgetsReducer from './components/Widgets/widgetsSlice';
import versionReducer from './components/versionSlice';
import appReducer from './views/appSlice';
import authReducer from "./components/authSlice";
import wsReducer from "./websocket/wsSlice";
import sitesReducer from "./components/Sites/sitesSlice";

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

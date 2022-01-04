/* eslint-disable import/no-cycle */
import { combineReducers } from 'redux';
import { History } from 'history';
import notebooksReducer from './components/Notebooks/notebooksSlice';
import tasksReducer from './tasks/tasksSlice';
import widgetsReducer from './components/Widgets/widgetsSlice';
import versionReducer from './components/versionSlice';

export default function createRootReducer(history: History) {
    return combineReducers({
        notebooks: notebooksReducer,
        tasks: tasksReducer,
        widgets: widgetsReducer,
        version: versionReducer,
    });
}

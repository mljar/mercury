/* eslint-disable import/no-cycle */
import { configureStore, getDefaultMiddleware, Action } from '@reduxjs/toolkit';
import { createBrowserHistory } from 'history';

import { ThunkAction } from 'redux-thunk';
import createRootReducer from './rootReducer';

export const history = createBrowserHistory();
const rootReducer = createRootReducer(history);
export type RootState = ReturnType<typeof rootReducer>;

const middleware = [...getDefaultMiddleware()]; // , router];

export const configuredStore = (initialState?: RootState) => {
  // Create Store
  const store = configureStore({
    reducer: rootReducer,
    middleware,
    preloadedState: initialState,
  });
  return store;
};
export type Store = ReturnType<typeof configuredStore>;
export type AppThunk = ThunkAction<void, RootState, unknown, Action<string>>;

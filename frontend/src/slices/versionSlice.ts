/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';

import { RootState } from '../store';
import { setToken, setUsername } from './authSlice';


const initialState = {
  fetchingIsPro: true,
  isPro: false,
  welcome: ""
};

const versionSlice = createSlice({
  name: 'version',
  initialState,
  reducers: {
    setVersion(state, action: PayloadAction<{ isPro: boolean }>) {
      const { isPro } = action.payload;
      state.isPro = isPro;
      state.fetchingIsPro = false;
    },
    setWelcome(state, action: PayloadAction<string>) {
      state.welcome = action.payload;
    }
  },
});

export default versionSlice.reducer;

export const {
  setVersion,
  setWelcome,
} = versionSlice.actions;

export const getIsPro = (state: RootState) => state.version.isPro;
export const getFetchingIsPro = (state: RootState) => state.version.fetchingIsPro;
export const getWelcome = (state: RootState) => state.version.welcome;

export const fetchVersion =
  () =>
    async (dispatch: Dispatch<AnyAction>) => {

      try {
        const url = '/api/v1/version/';
        const { data } = await axios.get(url);
        dispatch(setVersion(data));
      } catch (error) {
        console.log(`Problem during loading Mercury version. ${error}`);
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 401) {
            // clear auth data 
            dispatch(setToken(null));
            dispatch(setUsername(null));
            window.location.reload();
          }
        }
      }
    };


export const fetchWelcome =
  (siteId: number) =>
    async (dispatch: Dispatch<AnyAction>) => {

      try {
        const url = `/api/v1/${siteId}/welcome/`;
        const { data } = await axios.get(url);
        dispatch(setWelcome(data.msg));
      } catch (error) {
        console.log(`Problem during loading Mercury welcome message. ${error}`);
      }

    };


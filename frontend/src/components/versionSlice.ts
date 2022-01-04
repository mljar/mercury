/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from '@reduxjs/toolkit';
import axios from 'axios';

import { RootState } from '../store';


const initialState = {
  isPro: false,
};

const versionSlice = createSlice({
  name: 'version',
  initialState,
  reducers: {
    setVersion(state, action: PayloadAction<{ isPro: boolean }>) {
      const { isPro } = action.payload;
      state.isPro = isPro;
    },
  },
});

export default versionSlice.reducer;

export const {
  setVersion,
} = versionSlice.actions;

export const getIsPro = (state: RootState) => state.version.isPro;

export const fetchVersion =
  () =>
    async (dispatch: Dispatch<AnyAction>) => {

      try {
        const url = '/api/v1/version/';
        const { data } = await axios.get(url);
        dispatch(setVersion(data));
      } catch (error) {
        console.error(`Problem during loading Mercury version. ${error}`);
      }

    };


/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from "@reduxjs/toolkit";
import axios from "axios";

import { RootState } from "../../store";

export const SITE_PUBLIC = "PUBLIC";
export const SITE_PRIVATE = "PRIVATE";


export interface Site {
  id: number;
  title: string;
  slug: string;
  share: string;
  active: boolean;
  version: string;
  created_at: Date;
  updated_at: Date;
  created_by: number;
}


const initialState = {
  site: {} as Site,
};

const sitesSlice = createSlice({
  name: "sites",
  initialState,
  reducers: {
    setSite(
      state,
      action: PayloadAction<Site>
    ) {
      state.site = action.payload;
    },

  },
});

export default sitesSlice.reducer;

export const {
  setSite,
} = sitesSlice.actions;

export const getSite = (state: RootState) => state.sites.site;
export const isPublic = (state: RootState) => state.sites.site.share === SITE_PUBLIC;

export const fetchSite = () => async (dispatch: Dispatch<AnyAction>) => {
  try {
    console.log("fetchSite")
    dispatch(setSite({} as Site));
    const siteSlug = "single-site";
    const url = `/api/v1/get-site/${siteSlug}`;
    const { data } = await axios.get(url);
    console.log(data)
    dispatch(setSite(data as Site));
  } catch (error) {
    console.error(`Problem during loading site information. ${error}`);
  }
};

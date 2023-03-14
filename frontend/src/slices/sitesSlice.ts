/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from "@reduxjs/toolkit";
import axios, { AxiosError } from "axios";

import { RootState } from "../store";
import { setToken, setUsername } from "./authSlice";


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

export enum SiteStatus {
  Unknown = "Unknown",
  Loaded = "Loaded",
  NotFound = "Not found",
  AccessForbidden = "Access forbidden",
  NetworkError = "Network Error",
  PleaseRefresh = "Please refresh",
  LostConnection = "Lost connection",
}

const initialState = {
  site: {} as Site,
  siteStatus: SiteStatus.Unknown,
};

const sitesSlice = createSlice({
  name: "sites",
  initialState,
  reducers: {
    setSite(state, action: PayloadAction<Site>) {
      state.site = action.payload;
    },
    setSiteStatus(state, action: PayloadAction<SiteStatus>) {
      state.siteStatus = action.payload;
    }
  },
});

export default sitesSlice.reducer;

export const { setSite, setSiteStatus } = sitesSlice.actions;

export const getSite = (state: RootState) => state.sites.site;
export const getSiteStatus = (state: RootState) => state.sites.siteStatus;
export const getSiteId = (state: RootState) => state.sites.site.id;
export const isPublic = (state: RootState) => {
  return state.sites.site.share === SITE_PUBLIC;
};
export const fetchSite = () => async (dispatch: Dispatch<AnyAction>) => {
  try {
    dispatch(setSite({} as Site));
    dispatch(setSiteStatus(SiteStatus.Unknown));

    let siteSlug = "single-site";
    if(process.env.REACT_APP_SERVER_URL) {
      //siteSlug = window.location.origin;
      console.log("site ---")
      console.log( window.location.host)
      siteSlug = window.location.host.split('.')[0]
      console.log(siteSlug)
    }

    const url = `/api/v1/get-site/${siteSlug}/`;
    const { data } = await axios.get(url);

    dispatch(setSite(data as Site));
    dispatch(setSiteStatus(SiteStatus.Loaded));
  } catch (error) {
    const err = error as AxiosError;
    console.log(err.message)
    if (err?.message === "Network Error") {
      dispatch(setSiteStatus(SiteStatus.NetworkError));
    } else if (err.response!.status === 403) {
      dispatch(setSiteStatus(SiteStatus.AccessForbidden));
    } else if (err.response!.status === 404) {
      dispatch(setSiteStatus(SiteStatus.NotFound));
    } else if (err.response!.status === 401) {
      // invalid token, clear token ...
      dispatch(setToken(""));
      dispatch(setUsername(""));
      dispatch(setSiteStatus(SiteStatus.PleaseRefresh));
    } else {
      console.error(`Problem during loading site information. ${error}`);
    }
  }
};

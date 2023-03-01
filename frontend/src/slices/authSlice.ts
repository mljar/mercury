/* eslint-disable import/no-cycle */
import {
  createSlice,
  PayloadAction,
  AnyAction,
  Dispatch,
} from "@reduxjs/toolkit";
import axios, { AxiosError } from "axios";
import { NavigateFunction } from "react-router-dom";
import { toast } from "react-toastify";

import { RootState } from "../store";
import { setAxiosAuthToken } from "../utils";

let initToken = null;
if (localStorage.getItem("token")) {
  initToken = localStorage.getItem("token");
  setAxiosAuthToken(initToken);
}

type UserType = {
  pk: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
};

const initialState = {
  token: initToken as string | null,
  username: "" as string,
  user: {
    pk: 0,
    username: "",
    first_name: "",
    last_name: "",
    email: "",
  } as UserType,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setToken(state, action: PayloadAction<string | null>) {
      state.token = action.payload;
      setAxiosAuthToken(state.token);
      if (state.token) {
        localStorage.setItem("token", state.token);
      } else {
        localStorage.removeItem("token");
      }
    },
    setUsername(state, action: PayloadAction<string | null>) {
      state.username = action.payload ? action.payload : "";
      if (state.username && state.username !== "") {
        localStorage.setItem("username", state.username);
      } else {
        localStorage.removeItem("username");
      }
    },
    setUserInfo(state, action: PayloadAction<UserType>) {
      state.user = action.payload;
    },
  },
});

export default authSlice.reducer;

export const { setToken, setUsername, setUserInfo } = authSlice.actions;

export const getToken = (state: RootState) => state.auth.token;
export const getUsername = (state: RootState) => state.auth.username;
export const getUserInfo = (state: RootState) => state.auth.user;

export const fetchToken =
  (
    email: string,
    password: string,
    redirectPath: string,
    navigate: NavigateFunction
  ) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        const url = "/api/v1/auth/login/";
        const { data } = await axios.post(url, { email, password });

        dispatch(setToken(data.key));
        dispatch(setUsername(email.split("@")[0]));
        toast.success("Log in successfull");
        // redirect ...
        navigate(redirectPath);
      } catch (error) {
        const err = error as AxiosError;
        let msg = "Problem during authentication. ";
        if (err.response?.data?.non_field_errors !== undefined) {
          msg += err.response?.data?.non_field_errors;
        }
        toast.error(msg);
      }
    };

export const logout =
  (navigate: NavigateFunction) => async (dispatch: Dispatch<AnyAction>) => {
    try {
      const url = "/api/v1/auth/logout/";
      await axios.post(url);
      toast.success("Log out successfull");
      dispatch(setToken(""));
      dispatch(setUsername(""));
      navigate("/");
    } catch (error) {
      toast.error("Problem during log out");
    }
  };

export const fetchUserInfo = () => async (dispatch: Dispatch<AnyAction>) => {
  try {
    const url = "/api/v1/auth/user/";
    const { data } = await axios.get(url);
    dispatch(setUserInfo(data));
  } catch (error) {
    console.log(`Problem during getting user info. ${error}`);
  }
};

export const changePassword =
  (oldPassword: string, newPassword1: string, newPassword2: string) =>
    async (dispatch: Dispatch<AnyAction>) => {
      try {
        const url = "/api/v1/auth/password/change/";
        await axios.post(url, {
          old_password: oldPassword,
          new_password1: newPassword1,
          new_password2: newPassword2,
        });
        toast.success("Password changed successfully");
      } catch (error) {
        const err = error as AxiosError;
        if (err !== undefined && err.response !== undefined && err.response.data !== undefined) {
          const msg = Object.values(err.response.data);
          toast.error("Password not changed." + msg);
        } else {
          toast.error("Password not changed. Problem during password change.");
        }
      }
    };

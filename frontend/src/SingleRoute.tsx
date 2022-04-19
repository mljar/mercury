/* eslint react/jsx-props-no-spreading: off */
import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { setToken, setUsername } from "./components/authSlice";
import { fetchVersion } from "./components/versionSlice";
import { getSessionId } from "./utils";

import AppView from "./views/AppView";

export default function Routes() {
  const dispatch = useDispatch();

  useEffect(() => {
    getSessionId();
    dispatch(fetchVersion());
    if (localStorage.getItem("token")) {
      dispatch(setToken(localStorage.getItem("token")));
    }
    if (localStorage.getItem("username")) {
      dispatch(setUsername(localStorage.getItem("username")));
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AppView isSingleApp={true} notebookId={1} displayEmbed={true} />
  );
}
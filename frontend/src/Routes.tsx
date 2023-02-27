/* eslint react/jsx-props-no-spreading: off */
import React, { ReactNode, useEffect } from "react";
import { useDispatch } from "react-redux";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Outlet,
} from "react-router-dom";

import { setToken, setUsername } from "./components/authSlice";
import { fetchVersion } from "./components/versionSlice";
import { getSessionId } from "./utils";
import MainApp from "./views/App";
import AccountView from "./views/AccountView";
import HomeView from "./views/HomeView";
import LoginView from "./views/LoginView";
import { fetchSite } from "./components/Sites/sitesSlice";
type Props = {
  children: ReactNode;
};

function App(props: Props) {
  const { children } = props;
  return <>{children}</>;
}

export default function AppRoutes() {
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

    dispatch(fetchSite());

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Router>
      <App>
        <Routes>
          <Route path="/" element={<HomeView />} />
          <Route path="/app/:slug/:embed?" element={<MainApp />} />
          <Route path="/login" element={<LoginView />} />
          <Route path="/account" element={<AccountView />} />
        </Routes>
      </App>
    </Router>
  );
}

/* eslint react/jsx-props-no-spreading: off */
import React, { ReactNode, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Outlet,
} from "react-router-dom";

import { setToken, setUsername } from "./slices/authSlice";
// import { fetchVersion } from "./slices/versionSlice";
import { getSessionId } from "./utils";
import MainApp from "./views/App";
import AccountView from "./views/AccountView";
import HomeView from "./views/HomeView";
import LoginView from "./views/LoginView";
import { fetchSite, getSite } from "./slices/sitesSlice";
import RequireAuth from "./components/RequireAuth";
import Footer from "./components/Footer";
import HomeNavBar from "./components/HomeNavBar";
type Props = {
  children: ReactNode;
};

function App(props: Props) {
  const { children } = props;
  return <>{children}</>;
}

function AppLayout() {
  return (
    <RequireAuth>
      <>
        <Outlet />
      </>
    </RequireAuth>
  );
}

export default function AppRoutes() {
  const dispatch = useDispatch();

  const site = useSelector(getSite);

  useEffect(() => {
    getSessionId();
    // dispatch(fetchVersion());
    if (localStorage.getItem("token")) {
      dispatch(setToken(localStorage.getItem("token")));
    }
    if (localStorage.getItem("username")) {
      dispatch(setUsername(localStorage.getItem("username")));
    }

    dispatch(fetchSite());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  console.log(site, site.share === undefined);

  if (site.share === undefined) {
    return (
      <div className="App">
        <HomeNavBar isSitePublic={true} username={""} />
        <h1>Loading ...</h1>
        <Footer />
      </div>
    );
  }

  return (
    <Router>
      <App>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route path="/" element={<HomeView />} />
            <Route path="/app/:slug/:embed?" element={<MainApp />} />
            <Route path="/account" element={<AccountView />} />
          </Route>
          <Route path="/login" element={<LoginView />} />
        </Routes>
      </App>
    </Router>
  );
}

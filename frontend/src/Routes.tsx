/* eslint react/jsx-props-no-spreading: off */
import React, { ReactNode, useEffect } from "react";
import { useDispatch } from "react-redux";
import { Switch, Route } from "react-router-dom";
import { fetchVersion } from "./components/versionSlice";
import { getSessionId } from "./utils";

import AppView from "./views/AppView";
import HomeView from "./views/HomeView";
import LoginView from "./views/LoginView";
type Props = {
  children: ReactNode;
};

function App(props: Props) {
  const { children } = props;
  return <>{children}</>;
}

export default function Routes() {
  const dispatch = useDispatch();
  
  useEffect(() => {
    getSessionId();
    dispatch(fetchVersion());
  }, []);

  return (
    <App>
      <Switch>
        <Route exact path="/" component={HomeView} />
        <Route exact path="/app/:notebook_id/" component={AppView} />
        <Route exact path="/login" component={LoginView} />
      </Switch>
    </App>
  );
}

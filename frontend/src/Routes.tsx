/* eslint react/jsx-props-no-spreading: off */
import React, { ReactNode, useEffect } from "react";
import { Switch, Route } from "react-router-dom";
import { getSessionId } from "./utils";

import AppView from "./views/AppView";
import HomeView from "./views/HomeView";
type Props = {
  children: ReactNode;
};

function App(props: Props) {
  const { children } = props;
  return <>{children}</>;
}

export default function Routes() {
  useEffect(() => {
    getSessionId();
  }, []);

  return (
    <App>
      <Switch>
        <Route exact path="/" component={HomeView} />
        <Route exact path="/app/:notebook_id/" component={AppView} />
      </Switch>
    </App>
  );
}

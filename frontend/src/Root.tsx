import React from "react";
import { Provider } from "react-redux";
import { BrowserRouter as Router } from "react-router-dom";
import { History } from "history";
import { Store } from "./store";
import Routes from "./Routes";

type Props = {
  store: Store;
  history: History;
};
const Root = ({ store, history }: Props) => (
  <Provider store={store}>
    <Router>
      <Routes />
    </Router>
  </Provider>
);

export default Root;
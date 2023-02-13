import React from "react";
import { Provider } from "react-redux";
import { History } from "history";
import { Store } from "./store";
import Routes from "./Routes";

type Props = {
  store: Store;
  history: History;
};
const Root = ({ store, history }: Props) => (
  <Provider store={store}>
    <Routes />
  </Provider>
);

export default Root;

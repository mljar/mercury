import React from "react";
import { render } from "react-dom";
import axios from "axios";
import Root from "./Root";
import { history, configuredStore } from "./store";

import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "bootstrap/dist/js/bootstrap.min.js";
import "bootstrap/dist/css/bootstrap.css";
import "font-awesome/css/font-awesome.min.css";
import "react-block-ui/style.css";
import "filepond/dist/filepond.min.css";
import "filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css";
import "./index.css";

const store = configuredStore();

console.log("settings " + process.env.REACT_APP_SERVER_URL);
if (process.env.REACT_APP_SERVER_URL) {
  axios.defaults.baseURL = process.env.REACT_APP_SERVER_URL;
} else {
  if (window.location.origin === "http://localhost:3000") {
    axios.defaults.baseURL = "http://127.0.0.1:8000";
  } else {
    axios.defaults.baseURL = window.location.origin;
  }
  if (window.location.origin.startsWith("https://hf.space")) {
    axios.defaults.baseURL = window.location.href;
  }

  // in the case of some special params in the url
  axios.defaults.baseURL = axios.defaults.baseURL.split("+")[0];
  axios.defaults.baseURL = axios.defaults.baseURL.split("?")[0];
  axios.defaults.baseURL = axios.defaults.baseURL.split("#")[0];
}

console.log("set " + axios.defaults.baseURL)

document.addEventListener("DOMContentLoaded", () =>
  render(
    <div>
      <Root store={store} history={history} />
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={true}
        newestOnTop={true}
        closeOnClick
        pauseOnHover
      />
    </div>,
    document.getElementById("root")
  )
);

import React from "react";
import { render } from "react-dom";
import axios from "axios";
import Root from "./Root";
import { history, configuredStore } from "./store";

import "bootstrap/dist/js/bootstrap.min.js";
import "bootstrap/dist/css/bootstrap.css";
import "font-awesome/css/font-awesome.min.css";
import "react-block-ui/style.css";
import 'filepond/dist/filepond.min.css'
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css'
import "./index.css";

const store = configuredStore();

// new code
if (window.location.origin === "http://localhost:3000") {
  axios.defaults.baseURL = "http://127.0.0.1:8000";
} else {
  axios.defaults.baseURL = window.location.origin;
}


document.addEventListener("DOMContentLoaded", () =>
  render(
    <div>
      <Root store={store} history={history} />
    </div>,
    document.getElementById("root")
  )
);

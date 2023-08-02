/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function SiteNetworkErrorView() {
  return (
    <div className="App">
      <div
        style={{
          width: "100%",
          maxWidth: "500px",
          padding: "15px",
          margin: "0 auto",
        }}
      >
        <h3>Network Error</h3>
        <p>
          Please check if you have internet connection and server is running. In
          case of problems, please contact administrator.
        </p>
      </div>
    </div>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function LostConnection() {
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
        <h3>Lost connection</h3>
        <p>
          App lost connection to the server. Please try again in a moment or
          contact administrator.
        </p>
      </div>
    </div>
  );
}

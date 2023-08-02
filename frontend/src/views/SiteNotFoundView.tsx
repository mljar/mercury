/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function SiteNotFoundView() {
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
        <h3>Site does not exist</h3>
        <p>
          We can't find site you are looking for. Please make sure that URL
          address is correct.
        </p>
      </div>
    </div>
  );
}

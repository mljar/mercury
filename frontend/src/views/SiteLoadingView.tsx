/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function SiteLoadingView() {
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
        <p style={{ color: "gray" }}>Please wait. Loading site ...</p>
      </div>
    </div>
  );
}

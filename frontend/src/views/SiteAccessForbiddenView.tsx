/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { Link } from "react-router-dom";

export default function SiteAccessForbiddenView() {
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
        <h3>Access forbidden</h3>
        <p>
          Please <Link to="/login">login</Link> to access site.
        </p>
      </div>
    </div>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function SiteNotReadyView() {
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
        <h3>Site not ready</h3>
        <p>
          Your site is not ready yet. Please refresh page in a while or check
          the dashboard.
        </p>
        <button
          className="btn btn-success"
          onClick={() => window.location.reload()}
        >
          Refresh
        </button>
      </div>
    </div>
  );
}

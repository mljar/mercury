/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function NavBar() {
  return (
    <header className="navbar navbar-dark sticky-top bg-dark flex-md-nowrap p-0">
      <a className="navbar-brand col-md-3 col-lg-3 me-0 px-3" href="/">
        <img
          alt="Mercury"
          src={process.env.PUBLIC_URL + process.env.REACT_APP_LOCAL_URL + "/mercury_red.svg"}
          style={{ height: "24px" }}
        />
      </a>

      <button
        className="navbar-toggler position-absolute d-md-none collapsed"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#sidebarMenu"
        aria-controls="sidebarMenu"
        aria-expanded="false"
        aria-label="Toggle navigation"

      >
        <span className="navbar-toggler-icon" style={{ height: "15px", width: "15px" }}></span>
      </button>
    </header>
  );
}

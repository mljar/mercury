/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";

export default function NavBar() {
  return (
    <header className="navbar navbar-dark sticky-top bg-dark flex-md-nowrap p-0">
      <img
        alt="Mercury"
        src={process.env.PUBLIC_URL + process.env.REACT_APP_LOCAL_URL + "/mercury_red.svg"}
        style={{ height: "40px", marginLeft: "auto", marginRight: "auto" }}
      />
    </header>
  );
}

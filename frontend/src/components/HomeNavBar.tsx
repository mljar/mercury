/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import LoginButton from "./LoginButton";
import UserButton from "./UserButton";

type NavBarProps = {
  isSitePublic: boolean;
  username: string;
  logoSrc: string;
  navbarColor: string;
};

export default function NavBar({
  isSitePublic,
  username,
  logoSrc,
  navbarColor,
}: NavBarProps) {
  let headerBgClass = "";
  let headerStyle = {};
  if (navbarColor === "") {
    headerBgClass = "bg-dark";
  } else {
    headerStyle = {
      backgroundColor: navbarColor,
    };
  }

  return (
    <header
      className={`navbar navbar-dark sticky-top p-0 ${headerBgClass}`}
      style={headerStyle}
    >
      <div className="row" style={{ width: "100%", paddingRight: "0px" }}>
        <div className="col-4"></div>
        <div className="col-4 text-center">
          {logoSrc !== "" && logoSrc !== "loading" && (
            <a href="/">
              <img alt="" src={logoSrc} style={{ height: "40px" }} />
            </a>
          )}
          {logoSrc === "loading" && (
            <a href="/">
              <div style={{ height: "40px" }} />
            </a>
          )}
        </div>
        <div
          className="col-4"
          style={{ marginRight: "0px", paddingRight: "0px" }}
        >
          {!isSitePublic && username === "" && <LoginButton />}
          {username !== "" && <UserButton username={username} />}
        </div>
      </div>
    </header>
  );
}

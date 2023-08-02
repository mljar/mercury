/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { Link } from "react-router-dom";
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
      className={`navbar navbar-dark sticky-top ${headerBgClass} flex-md-nowrap p-0`}
      style={headerStyle}
    >
      <Link className="navbar-brand col-md-3 col-lg-3 me-0 px-3" to="/">
        {logoSrc !== "" && logoSrc !== "loading" && (
          <img
            alt=""
            src={logoSrc}
            style={{ height: "28px", paddingLeft: "10px" }}
          />
        )}
      </Link>

      {!isSitePublic && username === "" && <LoginButton />}
      {username !== "" && <UserButton username={username} />}
    </header>
  );
}

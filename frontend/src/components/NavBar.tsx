/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { Link } from "react-router-dom";
import LoginButton from "./LoginButton";
import UserButton from "./UserButton";

type NavBarProps = {
  isSitePublic: boolean;
  username: string;
};

export default function NavBar({ isSitePublic, username }: NavBarProps) {
  return (
    <header className="navbar navbar-dark sticky-top bg-dark flex-md-nowrap p-0">
      <Link className="navbar-brand col-md-3 col-lg-3 me-0 px-3" to="/">
        <img
          alt="Mercury"
          src={
            process.env.PUBLIC_URL +
            process.env.REACT_APP_LOCAL_URL +
            "/mercury_logo.svg"
          }
          style={{ height: "28px", paddingLeft: "10px" }} // height was 24px
        />
      </Link>

      {!isSitePublic && username === "" && <LoginButton />}
      {username !== "" && <UserButton username={username} />}
    </header>
  );
}

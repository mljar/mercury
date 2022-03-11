/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import LoginButton from "./LoginButton";
import UserButton from "./UserButton";

type NavBarProps = {
  isPro: boolean;
  username: string;
};

export default function NavBar({ isPro, username }: NavBarProps) {
  return (
    <header
      className="navbar navbar-dark sticky-top bg-dark p-0"
    >
      <div className="row" style={{ width: "100%", paddingRight: "0px" }}>
        <div className="col-4"></div>
        <div className="col-4 text-center">
          <a href="/">
            <img
              alt="Mercury"
              src={
                process.env.PUBLIC_URL +
                process.env.REACT_APP_LOCAL_URL +
                "/mercury_logo.svg"
              }
              style={{ height: "40px" }}
            />
          </a>
        </div>
        <div
          className="col-4"
          style={{ marginRight: "0px", paddingRight: "0px" }}
        >
          {isPro && username === "" && <LoginButton />}
          {isPro && username !== "" && <UserButton username={username} />}
        </div>
      </div>
    </header>
  );
}

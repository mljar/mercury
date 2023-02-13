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
    <header className="navbar navbar-dark sticky-top bg-dark flex-md-nowrap p-0">
      <a className="navbar-brand col-md-3 col-lg-3 me-0 px-3" href="/">
        {/* <i className="fa fa-home" aria-hidden="true"></i> {" "} */}
        <img
          alt="Mercury"
          src={
            process.env.PUBLIC_URL +
            process.env.REACT_APP_LOCAL_URL +
            "/mercury_logo.svg"
          }
          style={{ height: "28px", paddingLeft: "10px" }} // height was 24px
        />
      </a>

      {isPro && username === "" && <LoginButton />}
      {isPro && username !== "" && <UserButton username={username} />}
    </header>
  );
}

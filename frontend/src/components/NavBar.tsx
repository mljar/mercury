/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import { setView } from "../views/appSlice";
import LoginButton from "./LoginButton";
import UserButton from "./UserButton";

type NavBarProps = {
  showFiles: boolean;
  isPro: boolean;
  username: string;
};

export default function NavBar({ showFiles, isPro, username }: NavBarProps) {
  const dispatch = useDispatch();
  return (
    <header className="navbar navbar-dark sticky-top bg-dark flex-md-nowrap p-0">
      <a className="navbar-brand col-md-3 col-lg-3 me-0 px-3" href="/">
      <i className="fa fa-home" aria-hidden="true"></i> {" "}
        <img
          alt="Mercury"
          src={
            process.env.PUBLIC_URL +
            process.env.REACT_APP_LOCAL_URL +
            "/mercury_logo.svg"
          }
          style={{ height: "24px" }}
        />
      </a>

      {showFiles && (
        <ul className="nav col-12 col-lg-auto me-lg-auto mb-2 mb-md-0">
          <li>
            <button
              className="nav-link px-2 text-white"
              style={{
                background: "transparent",
                border: "none",
                fontSize: "0.9em",
              }}
              onClick={() => {
                dispatch(setView("app"));
              }}
            >
              <i className="fa fa-laptop" aria-hidden="true"></i> App
            </button>
          </li>
          <li>
            <button
              className="nav-link px-2 text-white"
              style={{
                background: "transparent",
                border: "none",
                fontSize: "0.9em",
              }}
              onClick={() => {
                dispatch(setView("files"));
              }}
            >
              <i className="fa fa-folder-open-o" aria-hidden="true"></i> Output
              Files
            </button>
          </li>
        </ul>
      )}

      {isPro && username === "" && <LoginButton />}
      {isPro && username !== "" && <UserButton username={username} />}

    </header>
  );
}

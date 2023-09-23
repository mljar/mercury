/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { logout } from "../slices/authSlice";

type UserButtonProps = {
  username: string;
};

export default function UserButton({ username }: UserButtonProps) {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  return (
    <div>
      <div className="dropdown" style={{ float: "right" }}>
        <a
          className="btn btn-secondary btn-sm dropdown-toggle"
          style={{ margin: "5px" }}
          href="#"
          role="button"
          id="dropdownMenuLink"
          data-bs-toggle="dropdown"
          aria-expanded="false"
        >
          {username}
        </a>

        <ul
          className="dropdown-menu dropdown-menu-end"
          aria-labelledby="dropdownMenuLink"
        >
          <li>
            <Link className="dropdown-item" to="/account">
              <i className="fa fa-user" aria-hidden="true"></i> Account
            </Link>
          </li>
          <li>
            <hr className="dropdown-divider" />
          </li>
          <li>
            <Link
              to={"/"}
              className="dropdown-item"
              onClick={() => dispatch(logout(navigate))}
            >
              <i className="fa fa-sign-out" aria-hidden="true"></i> Log out
            </Link>
          </li>
        </ul>
      </div>
    </div>
  );
}

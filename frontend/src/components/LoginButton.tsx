import React from "react";
import { Link } from "react-router-dom";

export default function LoginButton() {
  return (
    <div style={{ color: "white", padding: "5px", float: "right" }}>
      <Link to="/login" className="btn btn-primary btn-sm ">
        <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
      </Link>
    </div>
  );
}

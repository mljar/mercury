import React from "react";

export default function LoginButton() {
  return (
    <div style={{ color: "white", padding: "5px", float: "right" }}>
      <a href="/login" className="btn btn-primary btn-sm ">
        <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
      </a>
    </div>
  );
}

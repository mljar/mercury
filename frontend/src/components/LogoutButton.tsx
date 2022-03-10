import React from "react";

export default function LogoutButton() {
  return (
    <div style={{ color: "white", padding: "5px" }}>
      <a href="/logout" className="btn btn-primary btn-sm ">
        <i className="fa fa-sign-out" aria-hidden="true"></i> Log out
      </a>
    </div>
  );
}

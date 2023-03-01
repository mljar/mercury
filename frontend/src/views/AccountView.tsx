/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  changePassword,
  fetchUserInfo,
  getUserInfo,
  getUsername,
} from "../slices/authSlice";
import Footer from "../components/Footer";
import HomeNavBar from "../components/HomeNavBar";
import { isPublic } from "../slices/sitesSlice";

export default function AccountView() {
  const dispatch = useDispatch();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword1, setNewPassword1] = useState("");
  const [newPassword2, setNewPassword2] = useState("");
  const username = useSelector(getUsername);
  const user = useSelector(getUserInfo);
  const isSitePublic = useSelector(isPublic);

  document.body.style.backgroundColor = "white";

  useEffect(() => {
    dispatch(fetchUserInfo());
  }, [dispatch]);

  return (
    <div className="App">
      <HomeNavBar isSitePublic={isSitePublic} username={username} />

      <div className="container">
        <div className="mx-auto" style={{ width: "700px" }}>
          <div className="row" style={{ marginTop: "40px" }}>
            <h2>
              <i className="fa fa-user" aria-hidden="true"></i> Account
            </h2>
            <form>
              <div className="mb-3">
                <label className="form-label">Username</label>
                <input
                  className="form-control"
                  value={user.username}
                  disabled
                />
              </div>
              <div className="mb-3">
                <label className="form-label">First name</label>
                <input
                  className="form-control"
                  value={user.first_name}
                  disabled
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Last name</label>
                <input
                  className="form-control"
                  value={user.last_name}
                  disabled
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Email address</label>
                <input className="form-control" value={user.email} disabled />
              </div>
            </form>
          </div>
          <hr />
          <div className="row">
            <h2>
              <i className="fa fa-key" aria-hidden="true"></i> Change password
            </h2>
            <div>
              <div className="mb-3">
                <label className="form-label">Old password</label>
                <input
                  type="password"
                  className="form-control"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                />
              </div>
              <div className="mb-3">
                <label className="form-label">New password</label>
                <input
                  type="password"
                  className="form-control"
                  value={newPassword1}
                  onChange={(e) => setNewPassword1(e.target.value)}
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Repeat new password</label>
                <input
                  type="password"
                  className="form-control"
                  value={newPassword2}
                  onChange={(e) => setNewPassword2(e.target.value)}
                />
              </div>
              <div className="mb-3" style={{ paddingBottom: "50px" }}>
                <button
                  className="btn btn-primary"
                  onClick={() =>
                    dispatch(
                      changePassword(oldPassword, newPassword1, newPassword2)
                    )
                  }
                  disabled={
                    oldPassword === "" ||
                    newPassword1 === "" ||
                    newPassword2 === ""
                  }
                >
                  Change password
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

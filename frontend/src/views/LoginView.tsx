/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { withRouter } from "react-router-dom";
import { fetchToken } from "../components/authSlice";
import Footer from "../components/Footer";
import HomeNavBar from "../components/HomeNavBar";
import { getFetchingIsPro, getIsPro } from "../components/versionSlice";
import { useHistory } from "react-router-dom";
import ProFeatureAlert from "../components/ProFeatureAlert";

export default withRouter(function LoginView() {
  let history = useHistory();
  const dispatch = useDispatch();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const isPro = useSelector(getIsPro);
  const fetchingIsPro = useSelector(getFetchingIsPro);

  document.body.style.backgroundColor = "#f5f5f5";

  return (
    <div className="App">
      <HomeNavBar isPro={isPro} username={""} />

      {!isPro && !fetchingIsPro && (
        <ProFeatureAlert featureName={"authentication"} />
      )}
      {isPro && (
        <div className="div-signin text-center">
          <div className="form-signin">
            <h3 className="h3 mb-3 font-weight-normal">Please sign in</h3>
            <label className="sr-only">Username</label>
            <input
              type="username"
              id="inputUsername"
              className="form-control"
              placeholder="Username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
              }}
              required
            />
            <label className="sr-only">Password</label>
            <input
              type="password"
              id="inputPassword"
              className="form-control"
              placeholder="Password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
              required
            />
            <button
              className="btn btn-lg btn-primary btn-block"
              // type="submit"
              style={{ margin: "5px" }}
              onClick={() => {
                dispatch(fetchToken(username, password, history));
              }}
              disabled={username === "" || password === ""}
            >
              <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
            </button>
          </div>
          {/* <p className="text-muted">No account? Please contact the service administrator to create account.</p> */}
        </div>
      )}
      <Footer />
    </div>
  );
});

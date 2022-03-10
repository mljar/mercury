/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { withRouter } from "react-router-dom";
import Footer from "../components/Footer";
import HomeNavBar from "../components/HomeNavBar";
import { getIsPro } from "../components/versionSlice";

export default withRouter(function LoginView() {
  const dispatch = useDispatch();
  const isPro = useSelector(getIsPro);

  document.body.style.backgroundColor = "#f5f5f5";

  return (
    <div className="App">
      <HomeNavBar isPro={isPro} />
      {!isPro && (
        <div style={{ padding: "40px" }}>
          <div className="alert alert-primary mb-3" role="alert">
            <h5>
              <i className="fa fa-info-circle" aria-hidden="true"></i> The
              authentication is a Pro feature{" "}
            </h5>
            You are using an open-source version of the Mercury framework. The
            authentication is a Pro feature available for commercial users only.
            Please consider purchasing the Mercury commercial license. It is
            perpetual and comes with additional features, dedicated support, and
            allows white-labeling. You can learn more about available licenses
            on our{" "}
            <a
              href="https://mljar.com/pricing"
              target="_blank"
              rel="noreferrer"
            >
              website
            </a>
            .
            <br />
            <br />
            <br />
            <a href="/">
              <i className="fa fa-home" aria-hidden="true" /> Back to home
            </a>
          </div>
        </div>
      )}
      {isPro && (
        <div className="div-signin text-center">
          <form className="form-signin">
            <h3 className="h3 mb-3 font-weight-normal">Please sign in</h3>
            <label className="sr-only">Username</label>
            <input
              type="email"
              id="inputEmail"
              className="form-control"
              placeholder="Username"
              required
            />
            <label className="sr-only">Password</label>
            <input
              type="password"
              id="inputPassword"
              className="form-control"
              placeholder="Password"
              required
            />
            <button
              className="btn btn-lg btn-primary btn-block"
              type="submit"
              style={{ margin: "5px" }}
            >
              <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
            </button>
          </form>
          {/* <p className="text-muted">No account? Please contact the service administrator to create account.</p> */}
        </div>
      )}
      <Footer />
    </div>
  );
});

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import Footer from "../components/Footer";
import HomeNavBar from "../components/HomeNavBar";

export default function SitePleaseRefreshView() {
  return (
    <div className="App">
      <HomeNavBar isSitePublic={true} username={""} />
      <div
        style={{
          width: "100%",
          maxWidth: "500px",
          padding: "15px",
          margin: "0 auto",
        }}
      >
        <h3>Please refresh</h3>
        <p>
          Please try to refresh the website ...
        </p>
      </div>
      <Footer />
    </div>
  );
}

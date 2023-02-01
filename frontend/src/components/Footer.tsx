import React from "react";

export default function Footer() {
  return (
    <footer
      className="footer"
      style={{
        position: "absolute",
        bottom: "0",
        width: "100%",
        height: "40px",
        lineHeight: "40px",
        backgroundColor: "#f5f5f5",
        borderTop: "1px solid #e5e5e5",
      }}
    >
      <div className="container">
        <span className="text-muted" style={{ color: "gray" }}>
          Mercury ©{" "}
          <a
            style={{ textDecoration: "none", color: "gray" }}
            href="https://mljar.com"
            target="_blank"
            rel="noreferrer"
          >
            MLJAR
          </a>
        </span>
        <span className="text-muted" style={{ float: "right" }}>
          
          <a
            style={{ textDecoration: "none", color: "gray" }}
            href="https://github.com/mljar/mercury"
            target="_blank"
            rel="noreferrer"
          >
            Mercury
          </a>
          {" "}
          <i className="fa fa-github" aria-hidden="true"></i>
        </span>
      </div>
    </footer>
  );
}

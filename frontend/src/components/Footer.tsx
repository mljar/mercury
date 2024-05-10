import React from "react";

type FooterProps = {
  footerText: string;
};

export default function Footer({ footerText }: FooterProps) {
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
      {footerText === "" && (
        <div className="container" style={{ textAlign: "center"}}>
          
          <span className="text-muted" style={{ color: "gray", float: "left" }}>
            {" "}
            <a
              style={{ textDecoration: "none", color: "gray" }}
              href="/openapi"
            >
              OpenAPI
            </a>
          </span>

          <span className="text-muted" style={{ color: "gray", margin: "auto", display: "inline-block" }}>
            {" "}
            <a
              style={{ textDecoration: "none", color: "gray" }}
              href="https://runmercury.com"
              target="_blank"
              rel="noreferrer"
            >
              Notebooks served as Web Apps with Mercury
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
            </a>{" "}
            <i className="fa fa-github" aria-hidden="true"></i>
          </span>
        </div>
      )}
      {footerText !== "" && (
        <div
          className="container"
          style={{ color: "gray", textAlign: "center" }}
        >
          <span className="text-muted" style={{ color: "gray" }}>
            {footerText}
          </span>
        </div>
      )}
    </footer>
  );
}

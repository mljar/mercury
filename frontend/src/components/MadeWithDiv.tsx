import React from "react";

export default function MadeWithDiv() {
  return (
    <a href="https://runmercury.com" target="_blank" rel="noreferrer">
      <div className="poweredby">
        <div className="text-center">
          {" "}
          <b style={{ fontSize: "0.9em" }}>created with</b>{" "}
        </div>
        <div>
          <img
            alt="Mercury"
            src={
              process.env.PUBLIC_URL +
              process.env.REACT_APP_LOCAL_URL +
              "/mercury_black_logo.svg"
            }
            style={{ height: "27px" }}
          />
        </div>
      </div>
    </a>
  );
}

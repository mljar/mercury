import React from "react";

export default function MadeWithDiv() {
  return (
    <a href="https://mljar.com/mercury" target="_blank" rel="noreferrer">
      <div className="poweredby">
        {/* <div className="text-muted text-center"> Made with </div> */}
        <div>
          <img
            alt="Mercury"
            src={
              process.env.PUBLIC_URL +
              process.env.REACT_APP_LOCAL_URL +
              "/mercury_logo.svg"
            }
            style={{ height: "20px" }}
          />
        </div>
      </div>
    </a>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import axios from "axios";
import useWindowDimensions from "./WindowDimensions";

import BlockUi from "react-block-ui";
import { error } from "console";


type MainViewProps = {
  loadingState: string;
  notebookPath: string;
  waiting: boolean;
  errorMsg: string;
  watchMode: boolean;
};

export default function MainView({
  loadingState,
  notebookPath,
  waiting,
  errorMsg,
  watchMode,
}: MainViewProps) {
  const { height } = useWindowDimensions();

  return (
    <main
      className="col-md-9 ms-sm-auto col-lg-9"
      style={{ paddingTop: "0px", paddingRight: "0px", paddingLeft: "0px" }}
    >
      <BlockUi tag="div" blocking={waiting}>
        <div>
          {loadingState === "loading" && !watchMode && (
            <p>Loading notebook. Please wait ...</p>
          )}
          {loadingState === "error" && (
            <p>
              Problem while loading notebook. Please try again later or contact
              Mercury administrator.
            </p>
          )}
          {/* {waiting && (
          <div className="alert alert-primary mb-3" role="alert">
            Notebook is executed. Default notebook is presented below. New
            results will be loaded after execution.{" "}
            <i className="fa fa-coffee" aria-hidden="true"></i> Please wait ...
          </div>
        )} */}
          {errorMsg && (
            <div className="alert alert-danger mb-3" role="alert">
              <b>Notebook is executed with errors.</b>
              <p>{errorMsg}</p>
            </div>
          )}

          {errorMsg === "" && (
            <iframe
              width="100%"
              height={height - 58}
              src={`${axios.defaults.baseURL}${notebookPath}`}
              title="display"
            ></iframe>
          )}
        </div>
      </BlockUi>
    </main>
  );
}

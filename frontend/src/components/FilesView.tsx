/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import BlockUi from "react-block-ui";
import { setView } from "../slices/appSlice";
import FileItem from "./FileItem";

type FilesViewProps = {
  files: string[];
  filesState: string;
  waiting: boolean;
};

export default function FilesView({
  files,
  filesState,
  waiting,
}: FilesViewProps) {
  const dispatch = useDispatch();

  let filesLinks = [];

  for (let f of files) {
    let fname = f.split("/").pop();
    fname = fname?.split("?")[0];

    if (f && fname) {
      let downloadLink = `${axios.defaults.baseURL}${f}`;
      if (f.includes("s3.amazonaws.com")) {
        downloadLink = f;
      }
      filesLinks.push(
        <FileItem
          fname={fname}
          downloadLink={downloadLink}
          firstItem={f === files[0]}
          lastItem={f === files[files.length - 1]}
        />
      );
    }
  }

  return (
    <main className="col-md-9 ms-sm-auto col-lg-9" style={{ padding: "20px" }}>
      <div className="col-12" style={{ maxWidth: "900px" }}>
        <h3 style={{ paddingBottom: "10px" }}>
          <i className="fa fa-folder-open-o" aria-hidden="true"></i> Output
          Files
        </h3>
        <BlockUi tag="div" blocking={waiting}>
          <div>
            {filesState === "loaded" && filesLinks}
            {filesState === "loaded" && filesLinks.length === 0 && (
              <div>No files available for download</div>
            )}
            {filesState === "unknown" && (
              <p>Please run the notebook to produce output files ...</p>
            )}
            {filesState === "loading" && <p>Loading files please wait ...</p>}
            {filesState === "error" && (
              <div className="alert alert-danger mb-3" role="alert">
                There was an error during loading files. Please try to run the
                app again or contact the administrator.
              </div>
            )}
          </div>
        </BlockUi>
      </div>

      <button
        className="btn btn-secondary btn-sm"
        style={{ marginTop: "20px" }}
        onClick={() => {
          dispatch(setView("app"));
        }}
      >
        <i className="fa fa-arrow-left" aria-hidden="true"></i> Back to App
      </button>
    </main>
  );
}

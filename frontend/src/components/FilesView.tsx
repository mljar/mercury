/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import fileDownload from "js-file-download";
import BlockUi from "react-block-ui";
import { setView } from "../slices/appSlice";

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

  const handleDownload = (url: string, filename: string) => {
    axios
      .get(url, {
        responseType: "blob",
      })
      .then((res) => {
        fileDownload(res.data, filename);
      });
  };

  let filesLinks = [];

  for (let f of files) {
    let fname = f.split("/").pop();
    if (f && fname) {
      filesLinks.push(
        <div key={f}>
          <i
            className="fa fa-file-text-o"
            aria-hidden="true"
            style={{ paddingRight: "5px" }}
          ></i>{" "}
          <b>{fname}</b>
          <button
            style={{ float: "right" }}
            type="button"
            className="btn btn-primary"
            onClick={() =>
              handleDownload(`${axios.defaults.baseURL}${f}`, fname!)
            }
          >
            <i className="fa fa-download" aria-hidden="true"></i> Download
          </button>
          <hr />
        </div>
      );
    }
  }

  return (
    <main className="col-md-9 ms-sm-auto col-lg-9" style={{ padding: "20px" }}>
      <div className="col-8">
        <h3 style={{ paddingBottom: "10px" }}>
          <i className="fa fa-folder-open-o" aria-hidden="true"></i> Output Files
        </h3>
        <BlockUi tag="div" blocking={waiting}>
          <div>
            {filesState === "loaded" && filesLinks}
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
        // style={{ background: "transparent", border: "none", fontSize: "0.9em" }}
        onClick={() => {
          dispatch(setView("app"));
        }}
      >
        <i className="fa fa-arrow-left" aria-hidden="true"></i> Back to App
      </button>
    </main>
  );
}

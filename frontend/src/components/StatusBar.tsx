import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getSessionId, handleDownload } from "../utils";
import {
  WorkerState,
  WebSocketState,
  getWebSocketState,
  getWorkerState,
  getTryConnectCount,
} from "../slices/wsSlice";
import { getSiteId, setSiteStatus, SiteStatus } from "../slices/sitesSlice";
import axios from "axios";
import { exportToPDF, setExportingToPDF } from "../slices/tasksSlice";
import { setShowShareDialog } from "../slices/appSlice";

type Props = {
  allowDownload: boolean;
  allowShare: boolean;
  waiting: boolean;
  continuousUpdate: boolean;
  staticNotebook: boolean;
  notebookId: number;
  notebookPath: string;
  notebookTitle: string;
  runDownloadHTML: () => void;
  runDownloadPDF: () => void;
};

export default function StatusBar({
  allowDownload,
  allowShare,
  waiting,
  continuousUpdate,
  staticNotebook,
  notebookId,
  notebookPath,
  notebookTitle,
  runDownloadHTML,
  runDownloadPDF,
}: Props) {
  const dispatch = useDispatch();
  const wsStatus = useSelector(getWebSocketState);
  const workerState = useSelector(getWorkerState);
  const tryConnectCount = useSelector(getTryConnectCount);
  const siteId = useSelector(getSiteId);

  useEffect(() => {
    if (tryConnectCount >= 5) {
      dispatch(setSiteStatus(SiteStatus.LostConnection));
    }
  }, [dispatch, tryConnectCount]);

  let wifiColor = "orange";
  if (wsStatus === WebSocketState.Connected) {
    wifiColor = "green";
  } else if (
    wsStatus === WebSocketState.Disconnected ||
    wsStatus === WebSocketState.Unknown
  ) {
    wifiColor = "red";
  }

  let workerColor = "orange";
  if (workerState === WorkerState.Running || workerState === WorkerState.Busy) {
    workerColor = "green";
  } else if (
    workerState === WorkerState.Missing ||
    workerState === WorkerState.Unknown
  ) {
    workerColor = "red";
  }

  return (
    <div style={{ paddingBottom: "25px" }}>
      {notebookId !== undefined && !staticNotebook && (
        <>
          <span title={`WebSocket: ${wsStatus}`}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              fill={wifiColor}
              className="bi bi-wifi"
              viewBox="0 0 16 16"
            >
              <path d="M15.384 6.115a.485.485 0 0 0-.047-.736A12.444 12.444 0 0 0 8 3C5.259 3 2.723 3.882.663 5.379a.485.485 0 0 0-.048.736.518.518 0 0 0 .668.05A11.448 11.448 0 0 1 8 4c2.507 0 4.827.802 6.716 2.164.205.148.49.13.668-.049z" />
              <path d="M13.229 8.271a.482.482 0 0 0-.063-.745A9.455 9.455 0 0 0 8 6c-1.905 0-3.68.56-5.166 1.526a.48.48 0 0 0-.063.745.525.525 0 0 0 .652.065A8.46 8.46 0 0 1 8 7a8.46 8.46 0 0 1 4.576 1.336c.206.132.48.108.653-.065zm-2.183 2.183c.226-.226.185-.605-.1-.75A6.473 6.473 0 0 0 8 9c-1.06 0-2.062.254-2.946.704-.285.145-.326.524-.1.75l.015.015c.16.16.407.19.611.09A5.478 5.478 0 0 1 8 10c.868 0 1.69.201 2.42.56.203.1.45.07.61-.091l.016-.015zM9.06 12.44c.196-.196.198-.52-.04-.66A1.99 1.99 0 0 0 8 11.5a1.99 1.99 0 0 0-1.02.28c-.238.14-.236.464-.04.66l.706.706a.5.5 0 0 0 .707 0l.707-.707z" />
            </svg>
          </span>{" "}
          <span title={`Worker: ${workerState}\nSession Id: ${getSessionId()}`}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              fill={workerColor}
              className="bi bi-cpu"
              viewBox="0 0 16 16"
            >
              <path d="M5 0a.5.5 0 0 1 .5.5V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2h1V.5a.5.5 0 0 1 1 0V2A2.5 2.5 0 0 1 14 4.5h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14v1h1.5a.5.5 0 0 1 0 1H14a2.5 2.5 0 0 1-2.5 2.5v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14h-1v1.5a.5.5 0 0 1-1 0V14A2.5 2.5 0 0 1 2 11.5H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2v-1H.5a.5.5 0 0 1 0-1H2A2.5 2.5 0 0 1 4.5 2V.5A.5.5 0 0 1 5 0zm-.5 3A1.5 1.5 0 0 0 3 4.5v7A1.5 1.5 0 0 0 4.5 13h7a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 11.5 3h-7zM5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5v-3zM6.5 6a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z" />
            </svg>
          </span>
        </>
      )}
      {workerState === WorkerState.Busy && (
        <span title="Worker is busy">
          {" "}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            fill="green"
            className="bi bi-activity"
            viewBox="0 0 16 16"
          >
            <path
              fillRule="evenodd"
              d="M6 2a.5.5 0 0 1 .47.33L10 12.036l1.53-4.208A.5.5 0 0 1 12 7.5h3.5a.5.5 0 0 1 0 1h-3.15l-1.88 5.17a.5.5 0 0 1-.94 0L6 3.964 4.47 8.171A.5.5 0 0 1 4 8.5H.5a.5.5 0 0 1 0-1h3.15l1.88-5.17A.5.5 0 0 1 6 2Z"
            />
          </svg>
        </span>
      )}
      <div style={{ float: "right" }}>
        {allowDownload && (
          <div
            className="dropdown mx-2 btn-group"
            style={
              {
                //display: "inline",
                // width: "47%",
                // float: continuousUpdate ? "left" : "right",
              }
            }
          >
            <button
              className="btn btn-sm btn-primary dropdown-toggle"
              // style={{ margin: "0px", width: "100%" }}
              type="button"
              data-bs-toggle="dropdown"
              disabled={waiting}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ paddingBottom: "1px" }}
              >
                <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"></path>
                <path d="M7 11l5 5l5 -5"></path>
                <path d="M12 4l0 12"></path>
              </svg>{" "}
              Download
            </button>

            {/* dropdown-menu-end */}
            <ul className="dropdown-menu my-2">
              <li>
                <button
                  type="button"
                  style={{ cursor: "pointer" }}
                  className="dropdown-item"
                  onClick={() => {
                    if (staticNotebook) {
                      handleDownload(
                        `${axios.defaults.baseURL}${notebookPath}`,
                        `${notebookTitle}.html`
                      );
                    } else {
                      runDownloadHTML();
                    }
                  }}
                >
                  <i className="fa fa-file-code-o" aria-hidden="true"></i>{" "}
                  Download as HTML
                </button>
              </li>
              <li>
                <hr className="dropdown-divider" />
              </li>
              <li>
                <button
                  type="button"
                  className="dropdown-item"
                  onClick={() => {
                    if (staticNotebook) {
                      dispatch(exportToPDF(siteId, notebookId, notebookPath));
                    } else {
                      dispatch(setExportingToPDF(true));
                      runDownloadPDF();
                    }
                  }}
                >
                  <i className="fa fa-file-pdf-o" aria-hidden="true"></i>{" "}
                  Download as PDF
                </button>
              </li>
            </ul>
          </div>
        )}
        {allowShare && (
          <button
            className="btn btn-sm btn-primary"
            onClick={() => dispatch(setShowShareDialog(true))}
            disabled={waiting}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
              <path d="M6 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"></path>
              <path d="M18 6m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"></path>
              <path d="M18 18m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"></path>
              <path d="M8.7 10.7l6.6 -3.4"></path>
              <path d="M8.7 13.3l6.6 3.4"></path>
            </svg>{" "}
            Share
          </button>
        )}
      </div>
    </div>
  );
}

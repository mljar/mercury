/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useContext } from "react";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import {
  exportToPDF,
  scrapeSlidesHash,
  setExportingToPDF,
} from "../slices/tasksSlice";
import CheckboxWidget from "../widgets/Checkbox";
import NumericWidget from "../widgets/Numeric";
import RangeWidget from "../widgets/Range";
import SelectWidget from "../widgets/Select";
import SliderWidget from "../widgets/Slider";

import {
  isCheckboxWidget,
  isFileWidget,
  isNumericWidget,
  isRangeWidget,
  isSelectWidget,
  isSliderWidget,
  isTextWidget,
  isMarkdownWidget,
  IWidget,
  isOutputFilesWidget,
  isButtonWidget,
} from "../widgets/Types";
//import { getWidgetsValues, setWidgetValue } from "./Widgets/widgetsSlice";
import {
  getWidgetsValues,
  setSlidesHash,
  setWidgetValue,
} from "../slices/notebooksSlice";
import FileWidget from "../widgets/File";
import TextWidget from "../widgets/Text";
import { setShowSideBar, setView } from "../slices/appSlice";
import { handleDownload } from "../utils";
import MarkdownWidget from "../widgets/Markdown";

import { WebSocketContext } from "../websocket/Provider";
import WebSocketStateBar from "../websocket/StatusBar";
import {
  downloadHTML,
  downloadPDF,
  getWorkerState,
  runNotebook,
  WorkerState,
} from "../slices/wsSlice";
import ButtonWidget from "../widgets/Button";
import RunButton from "./RunButton";
import BlockUi from "react-block-ui";

type SideBarProps = {
  notebookTitle: string;
  notebookId: number;
  notebookSchedule: string;
  taskCreatedAt: Date;
  loadingState: string;
  waiting: boolean;
  widgetsParams: Record<string, IWidget>;
  watchMode: boolean;
  notebookPath: string;
  displayEmbed: boolean;
  showFiles: boolean;
  isPresentation: boolean;
  notebookParseErrors: string;
  continuousUpdate: boolean;
  staticNotebook: boolean;
  allowDownload: boolean;
};

export default function SideBar({
  notebookTitle,
  notebookId,
  notebookSchedule,
  taskCreatedAt,
  loadingState,
  waiting,
  widgetsParams,
  watchMode,
  notebookPath,
  displayEmbed,
  showFiles,
  isPresentation,
  notebookParseErrors,
  continuousUpdate,
  staticNotebook,
  allowDownload,
}: SideBarProps) {
  const dispatch = useDispatch();
  const widgetsValues = useSelector(getWidgetsValues);
  const workerState = useSelector(getWorkerState);

  const ws = useContext(WebSocketContext);

  const runNb = () => {
    if (continuousUpdate) {
      execNb();
    }
  };

  const execNb = () => {
    const slidesHash = scrapeSlidesHash();
    dispatch(setSlidesHash(slidesHash));

    ws.sendMessage(JSON.stringify(runNotebook(JSON.stringify(widgetsValues))));
  };

  // const saveNb = () => {
  //   if (!staticNotebook) {
  //     ws.sendMessage(JSON.stringify(saveNotebook()));
  //   }
  // };

  // const displayNb = (taskId: number) => {
  //   if (!staticNotebook) {
  //     ws.sendMessage(JSON.stringify(displayNotebook(taskId)));
  //   }
  // };

  const runDownloadHTML = () => {
    if (!staticNotebook) {
      ws.sendMessage(JSON.stringify(downloadHTML()));
    }
  };

  const runDownloadPDF = () => {
    if (!staticNotebook) {
      ws.sendMessage(JSON.stringify(downloadPDF()));
    }
  };

  useEffect(() => {
    if (widgetsParams) {
      for (let [key, widgetParams] of Object.entries(widgetsParams)) {
        if (key in widgetsValues) {
          continue;
        }

        if (widgetParams.input === "file") {
          dispatch(setWidgetValue({ key, value: [] as string[] }));
        } else if (widgetParams.input === "text") {
          dispatch(
            setWidgetValue({
              key,
              value: widgetParams.value ? widgetParams.value : "",
            })
          );
        } else if (isMarkdownWidget(widgetParams)) {
          // do nothing
          // dont put value into store
        } else if (isOutputFilesWidget(widgetParams)) {
          dispatch(setWidgetValue({ key, value: "output-dir" }));
        } else {
          dispatch(setWidgetValue({ key, value: widgetParams.value }));
        }
      }
    }
  }, [dispatch, widgetsParams, widgetsValues]);

  let widgets = [];
  let fileKeys = [] as string[]; // keys to file widgets, all need to be selected to enable RUN button

  if (widgetsParams && !staticNotebook) {
    // sort widgets keys based on cell index and code line number
    let widgetKeys = [];
    for (let key of Object.keys(widgetsParams)) {
      const parts = key.split(".");
      widgetKeys.push([key, parseFloat(`${parts[1]}.${parts[2]}`)]);
    }
    widgetKeys.sort(function (a, b) {
      const a1 = a[1] as number;
      const b1 = b[1] as number;
      return a1 - b1;
    });

    for (let wKey of widgetKeys) {
      const key = wKey[0] as string;
      const widgetParams = widgetsParams[key];

      if (isSelectWidget(widgetParams)) {
        widgets.push(
          <SelectWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as string}
            choices={widgetParams?.choices}
            multi={widgetParams?.multi}
            key={key}
            runNb={runNb}
          />
        );
      } else if (isCheckboxWidget(widgetParams)) {
        widgets.push(
          <CheckboxWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as boolean}
            key={key}
            runNb={runNb}
          />
        );
      } else if (isNumericWidget(widgetParams)) {
        widgets.push(
          <NumericWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as number}
            min={widgetParams?.min}
            max={widgetParams?.max}
            step={widgetParams?.step}
            key={key}
            runNb={runNb}
            continuousUpdate={continuousUpdate}
          />
        );
      } else if (isSliderWidget(widgetParams)) {
        widgets.push(
          <SliderWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as number}
            min={widgetParams?.min}
            max={widgetParams?.max}
            step={widgetParams?.step}
            vertical={widgetParams?.vertical}
            key={key}
            runNb={runNb}
          />
        );
      } else if (isRangeWidget(widgetParams)) {
        widgets.push(
          <RangeWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as [number, number]}
            min={widgetParams?.min}
            max={widgetParams?.max}
            step={widgetParams?.step}
            vertical={widgetParams?.vertical}
            key={key}
            runNb={runNb}
          />
        );
      } else if (isFileWidget(widgetParams)) {
        widgets.push(
          <FileWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            maxFileSize={widgetParams?.maxFileSize}
            key={key}
            value={widgetsValues[key] as string[]}
            runNb={runNb}
          />
        );
        fileKeys.push(key);
      } else if (isTextWidget(widgetParams)) {
        widgets.push(
          <TextWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as string}
            rows={widgetParams?.rows}
            key={key}
            runNb={runNb}
            continuousUpdate={continuousUpdate}
          />
        );
      } else if (isMarkdownWidget(widgetParams)) {
        widgets.push(
          <MarkdownWidget
            value={widgetParams.value as string}
            disabled={waiting}
            key={key}
          />
        );
      } else if (isButtonWidget(widgetParams)) {
        widgets.push(
          <ButtonWidget
            widgetKey={key}
            disabled={waiting}
            label={widgetParams?.label}
            value={widgetsValues[key] as boolean}
            style={widgetParams?.style}
            key={key}
            runNb={runNb}
          />
        );
      } else if (isOutputFilesWidget(widgetParams)) {
        // do nothing
      } else {
        console.log("Unknown widget type", widgetParams);
      }
    }
  }

  let additionalStyle = {};
  if (displayEmbed) {
    additionalStyle = { padding: "0px" };
  }

  const addSpaceInsteadTitle =
    notebookTitle === undefined ||
    notebookTitle === null ||
    notebookTitle === "";

  return (
    <nav
      id="sidebarMenu"
      className="col-lg-3 d-md-block bg-light sidebar"
      style={{ ...additionalStyle, overflowY: "auto" }}
    >
      <BlockUi blocking={false} message="">
        <div className="position-sticky p-3">
          <h4>
            {notebookTitle}
            <button
              className="btn btn-sm  btn-outline-primary"
              type="button"
              style={{
                float: "right",
                zIndex: "101",
              }}
              onClick={() => dispatch(setShowSideBar(false))}
              data-toggle="tooltip"
              data-placement="right"
              title="Hide sidebar"
            >
              <i className="fa fa-chevron-left" aria-hidden="true" />
            </button>
          </h4>

          <div style={{ padding: "0px" }}>
            <form>
              {widgets}
              {addSpaceInsteadTitle && <div style={{ padding: "15px" }}></div>}
              <div className="form-group mb-3 pb-1 pt-2">
                {!continuousUpdate && (
                  <RunButton
                    runNb={execNb}
                    waiting={waiting}
                    workerState={workerState}
                  />
                )}
                {allowDownload && (
                  <div
                    className="dropdown"
                    style={{
                      width: "47%",
                      float: continuousUpdate ? "left" : "right",
                    }}
                  >
                    <button
                      className="btn btn-primary dropdown-toggle"
                      style={{ margin: "0px", width: "100%" }}
                      type="button"
                      data-bs-toggle="dropdown"
                      disabled={waiting}
                    >
                      Download
                    </button>

                    <ul className="dropdown-menu dropdown-menu-end">
                      <li>
                        <a
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

                              //handleDownload(
                              //  `${axios.defaults.baseURL}${notebookPath}`,
                              //</li>  `${notebookTitle}.html`
                              //);
                            }
                          }}
                        >
                          <i
                            className="fa fa-file-code-o"
                            aria-hidden="true"
                          ></i>{" "}
                          Download as HTML
                        </a>
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
                              dispatch(exportToPDF(notebookId, notebookPath));
                            } else {
                              dispatch(setExportingToPDF(true));
                              runDownloadPDF();
                            }
                          }}
                        >
                          <i
                            className="fa fa-file-pdf-o"
                            aria-hidden="true"
                          ></i>{" "}
                          Download as PDF
                        </button>
                      </li>
                    </ul>
                  </div>
                )}
              </div>

              {/* {notebookSchedule !== "" && (
                <div className="alert alert-success mb-3" role="alert">
                  <p>
                    <i className="fa fa-clock-o" aria-hidden="true"></i>{" "}
                    Scheduled notebook at '{notebookSchedule}'.
                  </p>

                  {taskCreatedAt && (
                    <p>
                      {" "}
                      <i className="fa fa-calendar" aria-hidden="true"></i> Last
                      execution at {taskCreatedAt}.
                    </p>
                  )}
                  <div>
                    <i className="fa fa-refresh" aria-hidden="true"></i> Website
                    refresh every minute.
                  </div>
                </div>
              )} */}

              {continuousUpdate && (
                <div>
                  {/* add some space */}
                  <br />
                </div>
              )}

              {/* {waiting && workerState === WorkerState.Busy && (
                <div className="alert alert-success mb-3 mt-3" role="alert">
                  <i className="fa fa-cogs" aria-hidden="true"></i> Notebook is
                  executed. Please wait.
                </div>
              )} */}

              {waiting &&
                (workerState === WorkerState.Unknown ||
                  workerState === WorkerState.Queued) && (
                  <div className="alert alert-warning mb-3 mt-3" role="alert">
                    <i className="fa fa-cogs" aria-hidden="true"></i> Waiting
                    for worker ...
                  </div>
                )}
              {waiting && workerState === WorkerState.Starting && (
                <div className="alert alert-success mb-3 mt-3" role="alert">
                  <i className="fa fa-cogs" aria-hidden="true"></i> Initializing
                  worker ...
                </div>
              )}
              {watchMode && (
                <div className="alert alert-secondary mb-3 mt-3" role="alert">
                  <i className="fa fa-refresh" aria-hidden="true"></i> Notebook
                  in watch mode. All changes to Notebook will be automatically
                  visible in Mercury.
                </div>
              )}

              {isPresentation && (
                <div className="alert alert-primary mb-3" role="alert">
                  <i className="fa fa-television" aria-hidden="true"></i> Click
                  on presentation and press <b>F</b> for full screen. Press{" "}
                  <b>Esc</b> to quit.
                  <br />
                  <br />
                  <i className="fa fa-arrows" aria-hidden="true"></i> Click on
                  presentation and press <b>Esc</b> to navigate slides.
                </div>
              )}

              {/* {notebookParseErrors && (
                <div className="alert alert-danger mb-3" role="alert">
                  <i
                    className="fa fa-exclamation-circle"
                    aria-hidden="true"
                  ></i>{" "}
                  <b>Errors in the YAML</b>
                  <br />
                  {notebookParseErrors}
                </div>
              )} */}
            </form>
          </div>

          {/* <hr style={{ marginTop: "20px", marginBottom: "20px" }} />
          <div>
            {!watchMode && <SelectExecutionHistory disabled={waiting} displayNb={displayNb} />}
            {!staticNotebook && (
              <div>
                <button
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => {
                    saveNb();
                  }}
                  style={{ border: "none" }}
                  disabled={waiting}
                  title="Click to save current run"
                >
                  <i className="fa fa-floppy-o" aria-hidden="true"></i> Save run
                </button>
                <button
                  className="btn btn-sm btn-outline-danger"
                  onClick={() => {
                    dispatch(clearTasks(notebookId));
                    dispatch(fetchNotebook(notebookId));
                  }}
                  style={{ border: "none" }}
                  disabled={waiting}
                  title="Click to clear all previous runs of the notebook"
                >
                  <i className="fa fa-times-circle" aria-hidden="true"></i>{" "}
                  Delete runs
                </button>
              </div>
            )}
          </div>
           */}
          {showFiles && (
            <div>
              <hr />
              <button
                className="btn btn-sm btn-outline-secondary"
                style={{
                  border: "none",
                  //fontWeight: 500,
                }}
                onClick={() => {
                  dispatch(setView("app"));
                }}
              >
                <i className="fa fa-laptop" aria-hidden="true"></i> App
              </button>

              <button
                className="btn btn-sm btn-outline-secondary"
                style={{
                  border: "none",
                  //fontWeight: 500,
                }}
                onClick={() => {
                  dispatch(setView("files"));
                }}
              >
                <i className="fa fa-folder-open-o" aria-hidden="true"></i>{" "}
                Output Files
              </button>
            </div>
          )}
          {notebookId !== undefined && !staticNotebook && (
            <div>
              <hr />
              <div style={{ paddingLeft: "10px" }}>
                <WebSocketStateBar />{" "}
              </div>
            </div>
          )}
        </div>
      </BlockUi>
    </nav>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import { clearTasks, executeNotebook } from "../tasks/tasksSlice";
import CheckboxWidget from "./Widgets/Checkbox";
import NumericWidget from "./Widgets/Numeric";
import RangeWidget from "./Widgets/Range";
import SelectWidget from "./Widgets/Select";
import SliderWidget from "./Widgets/Slider";

import fileDownload from "js-file-download";

import {
  isCheckboxWidget,
  isFileWidget,
  isNumericWidget,
  isRangeWidget,
  isSelectWidget,
  isSliderWidget,
  isTextWidget,
  IWidget,
} from "./Widgets/Types";
import { getWidgetsValues, setWidgetValue } from "./Widgets/widgetsSlice";
import FileWidget from "./Widgets/File";
import TextWidget from "./Widgets/Text";

type SideBarProps = {
  notebookTitle: string;
  notebookId: number;
  loadingState: string;
  waiting: boolean;
  widgetsParams: Array<IWidget>;
  watchMode: boolean;
  notebookPath: string;
  displayEmbed: boolean;
};

export default function SideBar({
  notebookTitle,
  notebookId,
  loadingState,
  waiting,
  widgetsParams,
  watchMode,
  notebookPath,
  displayEmbed,
}: SideBarProps) {
  const dispatch = useDispatch();
  const widgetsValues = useSelector(getWidgetsValues);

  useEffect(() => {
    if (widgetsParams) {
      for (let [key, widgetParams] of Object.entries(widgetsParams)) {
        if (widgetParams.input === "file") {
          dispatch(setWidgetValue({ key, value: [] as string[] }));
        } else if (widgetParams.input === "text") {
          dispatch(
            setWidgetValue({
              key,
              value: widgetParams.value ? widgetParams.value : "",
            })
          );
        } else {
          dispatch(setWidgetValue({ key, value: widgetParams.value }));
        }
      }
    }
  }, [dispatch, widgetsParams]);

  let widgets = [];
  let fileKeys = [] as string[]; // keys to file widgets, all need to be selected to enable RUN button
  if (widgetsParams) {
    for (let [key, widgetParams] of Object.entries(widgetsParams)) {
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
          />
        );
      }
    }
  }

  const allFilesUploaded = () => {
    if (fileKeys.length === 0) {
      // no files at all, so OK
      return true;
    }
    for (const key of fileKeys) {
      if (!Object.prototype.hasOwnProperty.call(widgetsValues, key)) {
        return false;
      }
      let files = widgetsValues[key] as string[];
      if (files.length === 0) {
        return false;
      }
    }
    return true;
  };

  const handleDownload = (url: string, filename: string) => {
    axios
      .get(url, {
        responseType: "blob",
      })
      .then((res) => {
        fileDownload(res.data, filename);
      });
  };

  let additionalStyle = {};
  if (displayEmbed) {
    additionalStyle = { padding: "0px" };
  }

  return (
    <nav
      id="sidebarMenu"
      className="col-md-3 col-lg-3 d-md-block bg-light sidebar collapse"
      style={{ ...additionalStyle, overflowY: "auto" }}
    >
      <div className="position-sticky p-3">
        <h4>{notebookTitle}</h4>
        <div style={{ padding: "0px" }}>
          <form>
            {widgets}

            <div className="form-group mb-3">
              <button
                type="button"
                className="btn btn-success"
                style={{ marginRight: "10px", width: "47%" }}
                onClick={() => dispatch(executeNotebook(notebookId))}
                disabled={waiting || !allFilesUploaded()}
              >
                <i className="fa fa-play" aria-hidden="true"></i> Run
              </button>

              <button
                style={{ width: "47%", float: "right" }}
                type="button"
                className="btn btn-primary"
                disabled={waiting}
                onClick={() =>
                  handleDownload(
                    `${axios.defaults.baseURL}${notebookPath}`,
                    `${notebookTitle}.html`
                  )
                }
              >
                <i className="fa fa-download" aria-hidden="true"></i> Download
              </button>
            </div>

            {fileKeys && !allFilesUploaded() && (
              <div className="alert alert-danger mb-3" role="alert">
                <i className="fa fa-file" aria-hidden="true"></i> Please upload
                all required files.
              </div>
            )}

            {notebookTitle === "Please provide title" && (
              <div className="alert alert-warning mb-3" role="alert">
                <i
                  className="fa fa-exclamation-triangle"
                  aria-hidden="true"
                ></i>{" "}
                <b>
                  Please add YAML config to your notebook as a first raw cell.
                </b>
                <br />
                <br />
                Example:
                <pre>
                  ---
                  <br />
                  title: Report title
                  <br />
                  author: Your name
                  <br />
                  description: My amazing report
                  <br />
                  ---
                </pre>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() =>
                    window.open(
                      "https://github.com/mljar/mercury#convert-notebook-to-web-app-with-yaml",
                      "_blank"
                    )
                  }
                >
                  <i className="fa fa-book" aria-hidden="true"></i> Read more
                </button>
              </div>
            )}

            {waiting && (
              <div className="alert alert-primary mb-3" role="alert">
                <i className="fa fa-cogs" aria-hidden="true"></i> Notebook is
                executed. Please wait.
              </div>
            )}
            {watchMode && (
              <div className="alert alert-secondary mb-3" role="alert">
                <i className="fa fa-refresh" aria-hidden="true"></i> Notebook in
                watch mode. All changes to Notebook will be automatically
                visible in Mercury.
              </div>
            )}
          </form>
        </div>
        <hr style={{ marginTop: "50px", marginBottom: "10px" }} />
        <div>
          <button
            className="btn btn-sm btn-outline-danger"
            onClick={() => {
              dispatch(clearTasks(notebookId));
            }}
            style={{ border: "none" }}
            disabled={waiting}
            title="Click to clear all previous runs of the notebook"
          >
            <i className="fa fa-times-circle" aria-hidden="true"></i> Clear
            tasks
          </button>
        </div>
      </div>
    </nav>
  );
}

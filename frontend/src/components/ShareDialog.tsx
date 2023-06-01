import React from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  isCheckboxWidget,
  isNumericWidget,
  isRangeWidget,
  isSelectWidget,
  isSliderWidget,
  isTextWidget,
  IWidget,
} from "../widgets/Types";
import { getWidgetsValues, WidgetValueType } from "../slices/notebooksSlice";
import { getShowShareDialog, setShowShareDialog } from "../slices/appSlice";

type Props = {
  //widgetsValues: Record<string, WidgetValueType>;
  widgetsParams: Record<string, IWidget>;
};

export default function ShareDialog({
  //widgetsValues,
  widgetsParams,
}: Props) {
  const dispatch = useDispatch();
  const showShareDialog = useSelector(getShowShareDialog);
  const widgetsValues: Record<string, WidgetValueType> = useSelector(
    getWidgetsValues
  ) as Record<string, WidgetValueType>;

  let noUrlKeys = true;
  let urlParams = "?";
  if (
    widgetsParams !== undefined &&
    widgetsParams !== null &&
    widgetsValues !== undefined &&
    widgetsValues !== null
  ) {
    for (let [key, widgetParams] of Object.entries(widgetsParams)) {
      if (widgetsValues[key] === undefined) {
        continue;
      }

      if (
        isCheckboxWidget(widgetParams) ||
        isNumericWidget(widgetParams) ||
        isRangeWidget(widgetParams) ||
        isSelectWidget(widgetParams) ||
        isSliderWidget(widgetParams) ||
        isTextWidget(widgetParams)
      ) {
        if (widgetParams?.url_key !== null && widgetParams?.url_key !== "") {
          noUrlKeys = false;
        }
      }

      if (
        isCheckboxWidget(widgetParams) ||
        isNumericWidget(widgetParams) ||
        isSliderWidget(widgetParams) ||
        isTextWidget(widgetParams)
      ) {
        if (widgetParams?.url_key !== null && widgetParams?.url_key !== "") {
          urlParams += `${widgetParams?.url_key}=${widgetsValues[key]}&`;
        }
      }

      if (isRangeWidget(widgetParams)) {
        if (widgetParams?.url_key !== null && widgetParams?.url_key !== "") {
          const v = widgetsValues[key] as [number, number];

          urlParams += `${widgetParams?.url_key}=${v[0]},${v[1]}&`;
        }
      }
      if (isSelectWidget(widgetParams)) {
        if (widgetParams?.url_key !== null && widgetParams?.url_key !== "") {
          if (widgetParams?.multi) {
            const v = widgetsValues[key] as string[];

            urlParams += `${widgetParams?.url_key}=${v.join(",")}&`;
          } else {
            const v = widgetsValues[key] as string;
            urlParams += `${widgetParams?.url_key}=${v}&`;
          }
        }
      }
    }
    if (urlParams !== "?") {
      urlParams = urlParams.slice(0, urlParams.length - 1);
    }
  }

  return (
    <div
      className=""
      style={{
        position: "fixed",
        top: "0",
        left: "0",
        width: "100%",
        height: "100%",
        background: "rgba(0, 0, 0, 0.6)",
        display: showShareDialog ? "block" : "none",
        zIndex: 100
      }}
    >
      <section
        className=""
        style={{
          position: "fixed",
          width: "100%",
          height: "auto",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
        }}
      >
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
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
              </h3>
              <button
                type="button"
                className="btn-close"
                aria-label="Close"
                onClick={() => dispatch(setShowShareDialog(false))}
              ></button>
            </div>
            <div className="modal-body">
              <div className="py-2">
                <label>App address</label>
                <input
                  type="text"
                  className="form-control"
                  disabled={true}
                  value={window.location.origin + window.location.pathname}
                ></input>
              </div>

              {!noUrlKeys && (
                <div className="py-2">
                  <label>App address with current paramters</label>
                  <textarea
                    rows={5}
                    className="form-control"
                    disabled={true}
                    value={window.location.origin + window.location.pathname + urlParams}
                  />
                </div>
              )}
              {noUrlKeys && (
                <div className="py-2">
                  There are no <code>url_key</code> defined for any widget. You
                  can easily share URL to your notebook with preset values by
                  using <code>url_key</code> in the widget. Please check{" "}
                  <a
                    href="https://runmercury.com/docs/input-widgets/"
                    target="_blank"
                    rel="noreferrer"
                  >
                    documentation
                  </a>
                  .
                </div>
              )}
              <div className="py-2"></div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => dispatch(setShowShareDialog(false))}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

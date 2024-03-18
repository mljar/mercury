import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useSearchParams } from "react-router-dom";
import { setUrlValuesUsed, setWidgetUrlValue, setWidgetValue } from "../slices/notebooksSlice";

type TextProps = {
  widgetKey: string;
  label: string | null;
  value: string | undefined;
  rows: number | null;
  disabled: boolean;
  hidden: boolean;
  runNb: () => void;
  continuousUpdate: boolean;
  url_key: string;
  sanitize: boolean;
};

export default function TextWidget({
  widgetKey,
  label,
  value,
  rows,
  disabled,
  hidden,
  runNb,
  continuousUpdate,
  url_key,
  sanitize,
}: TextProps) {
  const dispatch = useDispatch();
  const [apply, showApply] = useState(false);
  const [updated, userInteraction] = useState(false);
  let rowsValue: number = rows ? rows : 1;

  const sanitizeString = (input_string: string) => {
    return input_string.replace(/["'(){}[\]`^]/gim, "");
  };

  const [searchParams] = useSearchParams();
  useEffect(() => {
    if (url_key !== undefined && url_key !== "") {
      const urlValue = searchParams.get(url_key);
      if (!updated && urlValue !== undefined && urlValue !== null) {
        dispatch(
          setWidgetUrlValue({
            key: widgetKey,
            value: urlValue,
          })
        );
        dispatch(setUrlValuesUsed(true));
      }
    }
  }, [dispatch, searchParams, updated, url_key, widgetKey]);

  return (
    <div className="form-group mb-3" style={{ display: hidden ? "none" : "" }}>
      <label
        htmlFor={`textarea-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
      {rowsValue === 1 && (
        <input
          className="form-control"
          type="text"
          id={`text-${label}`}
          value={value ? value : ""}
          onChange={(e) => {
            userInteraction(true);
            showApply(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: sanitize ? sanitizeString(e.target.value) : e.target.value,
              })
            );
          }}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              runNb();
              showApply(false);
              e.preventDefault();
            }
          }}
          disabled={disabled}
        />
      )}
      {rowsValue > 1 && (
        <textarea
          className="form-control"
          id={`text-area-${label}`}
          rows={rowsValue}
          value={value ? value : ""}
          onChange={(e) => {
            userInteraction(true);
            showApply(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: sanitize ? sanitizeString(e.target.value) : e.target.value,
              })
            );
          }}
          disabled={disabled}
        />
      )}

      {apply && continuousUpdate && rowsValue === 1 && (
        // <div
        //   style={{
        //     fontSize: "0.7em",
        //     float: "right",
        //     position: "relative",
        //     top: "0px",
        //     left: "-5px",
        //     color: "#2684ff",
        //   }}
        // >
        //   Press enter to apply
        // </div>

        <div
          style={{
            float: "right",
            position: "relative",
            top: "2px",
            left: "0px",
          }}
        >
          <button
            className="btn btn-sm btn-outline-primary"
            onClick={(e) => {
              runNb();
              showApply(false);
              e.preventDefault();
            }}
            style={{
              fontSize: "0.7em",
              border: "none",
            }}
          >
            Press enter or click to apply
          </button>
        </div>
      )}
      {apply && continuousUpdate && rowsValue > 1 && (
        <div
          style={{
            float: "right",
            position: "relative",
            top: "2px",
            left: "0px",
          }}
        >
          <button
            className="btn btn-sm btn-outline-primary"
            onClick={(e) => {
              runNb();
              showApply(false);
              e.preventDefault();
            }}
            style={{
              fontSize: "0.7em",
              border: "none",
            }}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}

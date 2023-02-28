import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "../slices/notebooksSlice";

type TextProps = {
  widgetKey: string;
  label: string | null;
  value: string | undefined;
  rows: number | null;
  disabled: boolean;
  runNb: () => void;
  continuousUpdate: boolean;
};

export default function TextWidget({
  widgetKey,
  label,
  value,
  rows,
  disabled,
  runNb,
  continuousUpdate,
}: TextProps) {
  const dispatch = useDispatch();
  const [apply, showApply] = useState(false);
  let rowsValue: number = rows ? rows : 1;

  const sanitizeString = (input_string: string) => {
    return input_string.replace(/["'(){}[\]`^]/gim, "");
  };

  return (
    <div className="form-group mb-3">
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
            showApply(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: sanitizeString(e.target.value),
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
            showApply(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: sanitizeString(e.target.value),
              })
            );
          }}
          disabled={disabled}
        />
      )}

      {apply && continuousUpdate && rowsValue === 1 && (
        <div
          style={{
            fontSize: "0.7em",
            float: "right",
            position: "relative",
            top: "0px",
            left: "-5px",
            color: "#2684ff",
          }}
        >
          Press enter to apply
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
            }}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}

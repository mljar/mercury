import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import {
  setWidgetValue,
} from "../slices/notebooksSlice";

type ButtonProps = {
  widgetKey: string;
  label: string | null;
  style: string;
  value: string | boolean | null;
  disabled: boolean;
  runNb: () => void;
};

export default function ButtonWidget({
  widgetKey,
  label,
  style,
  value,
  disabled,
  runNb,
}: ButtonProps) {
  const dispatch = useDispatch();

  let selectedClass = "btn-primary";
  if (style === "success") {
    selectedClass = "btn-success";
  } else if (style === "danger") {
    selectedClass = "btn-danger";
  } else if (style === "info") {
    selectedClass = "btn-info";
  } else if (style === "warning") {
    selectedClass = "btn-warning";
  }

  useEffect(() => {
    if (value) {
      runNb();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="form-group mb-3">
      <button
        type="button"
        className={`btn ${selectedClass}`}
        style={{ marginRight: "10px", width: "47%" }}
        onClick={() => {
          dispatch(
            setWidgetValue({
              key: widgetKey,
              value: true,
            })
          );
        }}
        disabled={disabled}
      >
        {label}
      </button>
    </div>
  );
}

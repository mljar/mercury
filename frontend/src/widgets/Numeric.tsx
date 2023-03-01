import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "../slices/notebooksSlice";

type NumericProps = {
  widgetKey: string;
  label: string | null;
  value: number | null;
  min: number | null;
  max: number | null;
  step: number | null;
  disabled: boolean;
  runNb: () => void;
  continuousUpdate: boolean;
};

export default function NumericWidget({
  widgetKey,
  label,
  value,
  min,
  max,
  step,
  disabled,
  runNb,
  continuousUpdate,
}: NumericProps) {
  const dispatch = useDispatch();
  const [apply, showApply] = useState(false);

  let minValue = undefined;
  let maxValue = undefined;
  let stepValue = 1;
  if (min) {
    minValue = min;
  }
  if (max) {
    maxValue = max;
  }
  if (step) {
    stepValue = step;
  }

  let displayValue: string | number = "";
  if (value) {
    displayValue = value;
  }

  const validateValue = () => {
    if (min && value && value < min) {
      dispatch(setWidgetValue({ key: widgetKey, value: min }));
    }
    if (max && value && value > max) {
      dispatch(setWidgetValue({ key: widgetKey, value: max }));
    }
  };

  return (
    <div className="form-group mb-3">
      <label
        htmlFor={`checkbox-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
      <input
        className="form-control"
        type="number"
        value={displayValue as number | string}
        onChange={(e) => {
          showApply(true);
          dispatch(setWidgetValue({ key: widgetKey, value: e.target.value }));
        }}
        onBlur={(e) => {
          validateValue();
        }}
        onKeyPress={(e) => {
          if (e.key === "Enter") {
            validateValue();
            runNb();
            showApply(false);
            e.preventDefault();
          }
        }}
        min={minValue}
        max={maxValue}
        step={stepValue}
      />
      {apply && continuousUpdate && (
        <div
          style={{
            float: "right",
            position: "relative",
            top: "0px",
            left: "0px",
          }}
        >
          <button
            className="btn btn-sm btn-outline-primary"
            onClick={(e) => {
              validateValue();
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
    </div>
  );
}

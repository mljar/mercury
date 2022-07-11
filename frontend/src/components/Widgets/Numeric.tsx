import React from "react";
import NumericInput from "react-numeric-input";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "./widgetsSlice";

type NumericProps = {
  widgetKey: string;
  label: string | null;
  value: number | null;
  min: number | null;
  max: number | null;
  step: number | null;
  disabled: boolean;
};

export default function NumericWidget({
  widgetKey,
  label,
  value,
  min,
  max,
  step,
  disabled,
}: NumericProps) {
  const dispatch = useDispatch();

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

  return (
    <div className="form-group mb-3">
      <label htmlFor={`checkbox-${label}`}>{label}</label>
      <NumericInput
        className="form-control"
        disabled={disabled}
        value={value as number}
        min={minValue}
        max={maxValue}
        step={stepValue}
        onChange={(e) => {
          dispatch(setWidgetValue({ key: widgetKey, value: e }));
        }}
        onBlur={(e) => {
          if (min && value && value < min) {
            dispatch(setWidgetValue({ key: widgetKey, value: min }));
          }
          if (max && value && value > max) {
            dispatch(setWidgetValue({ key: widgetKey, value: max }));
          }
        }}
      />
    </div>
  );
}

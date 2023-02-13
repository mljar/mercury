import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { RUN_DELAY, setWidgetValue } from "../Notebooks/notebooksSlice";

type NumericProps = {
  widgetKey: string;
  label: string | null;
  value: number | null;
  min: number | null;
  max: number | null;
  step: number | null;
  disabled: boolean;
  runNb: () => void;
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
}: NumericProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);

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

  useEffect(() => {
    if (!updated) return;
    const timeOutId = setTimeout(() => {
      //console.log("run from numeric");
      runNb();
    }, RUN_DELAY);
    return () => clearTimeout(timeOutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

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
          userInteraction(true);
          dispatch(setWidgetValue({ key: widgetKey, value: e.target.value }));
        }}
        onBlur={(e) => {
          userInteraction(true);
          if (min && value && value < min) {
            dispatch(setWidgetValue({ key: widgetKey, value: min }));
          }
          if (max && value && value > max) {
            dispatch(setWidgetValue({ key: widgetKey, value: max }));
          }
        }}
        min={minValue}
        max={maxValue}
        step={stepValue}
      />
    </div>
  );
}

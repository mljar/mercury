import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useSearchParams } from "react-router-dom";
import {
  setUrlValuesUsed,
  setWidgetUrlValue,
  setWidgetValue,
} from "../slices/notebooksSlice";

type NumericProps = {
  widgetKey: string;
  label: string | null;
  value: number | null;
  min: number | null;
  max: number | null;
  step: number | null;
  disabled: boolean;
  hidden: boolean;
  runNb: () => void;
  continuousUpdate: boolean;
  url_key: string;
};

export default function NumericWidget({
  widgetKey,
  label,
  value,
  min,
  max,
  step,
  disabled,
  hidden,
  runNb,
  continuousUpdate,
  url_key,
}: NumericProps) {
  const dispatch = useDispatch();
  const [apply, showApply] = useState(false);
  const [updated, userInteraction] = useState(false);

  let minValue = 0;
  let maxValue = 10;
  let stepValue = 1;
  if (min !== null) {
    minValue = min;
  }
  if (max !== null) {
    maxValue = max;
  }
  if (step !== null) {
    stepValue = step;
  }
  let displayValue = value !== null && value !== undefined ? value : 0;

  const [searchParams] = useSearchParams();
  useEffect(() => {
    if (url_key !== undefined && url_key !== "") {
      const urlValue = searchParams.get(url_key);
      if (
        !updated &&
        urlValue !== undefined &&
        urlValue !== null &&
        !isNaN(parseFloat(urlValue)) &&
        parseFloat(urlValue) >= minValue &&
        parseFloat(urlValue) <= maxValue
      ) {
        dispatch(
          setWidgetUrlValue({
            key: widgetKey,
            value: parseFloat(urlValue),
          })
        );
        dispatch(setUrlValuesUsed(true));
      }
    }
  }, [dispatch, maxValue, minValue, searchParams, updated, url_key, widgetKey]);

  const validateValue = () => {
    if (min !== null && value !== null && value < min) {
      dispatch(setWidgetValue({ key: widgetKey, value: min }));
    }
    if (max !== null && value !== null && value > max) {
      dispatch(setWidgetValue({ key: widgetKey, value: max }));
    }
  };

  return (
    <div className="form-group mb-3" style={{ display: hidden ? "none" : "" }}>
      <label
        htmlFor={`checkbox-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
      <input
        className="form-control"
        type="number"
        value={displayValue} // {displayValue as number | string}
        onChange={(e) => {
          userInteraction(true);
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
        disabled={disabled}
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

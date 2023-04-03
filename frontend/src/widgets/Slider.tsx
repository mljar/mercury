import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import {
  setUrlValuesUsed,
  setWidgetUrlValue,
  setWidgetValue,
} from "../slices/notebooksSlice";
import { Range, getTrackBackground } from "react-range";
import { useSearchParams } from "react-router-dom";

type SliderProps = {
  widgetKey: string;
  label: string | null;
  value: number | null;
  min: number | null;
  max: number | null;
  step: number | null;
  vertical: boolean | null;
  disabled: boolean;
  hidden: boolean;
  runNb: () => void;
  url_key: string;
};

export default function SliderWidget({
  widgetKey,
  label,
  value,
  min,
  max,
  step,
  vertical,
  disabled,
  hidden,
  runNb,
  url_key,
}: SliderProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);

  let minValue = 0;
  let maxValue = 100;
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

  const vals: number[] = [value !== null ? value : maxValue];

  return (
    <div className="form-group mb-3" style={{ display: hidden ? "none" : "" }}>
      <label
        htmlFor={`slider-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>

      <div
        style={{
          paddingTop: "12px",
          display: "flex",
          justifyContent: "center",
          flexWrap: "wrap",
        }}
      >
        <Range
          disabled={disabled}
          values={vals}
          step={stepValue}
          min={minValue}
          max={maxValue}
          onChange={(values) => {
            userInteraction(true);
            dispatch(setWidgetValue({ key: widgetKey, value: values[0] }));
          }}
          onFinalChange={(values) => {
            runNb();
          }}
          renderTrack={({ props, children }) => (
            <div
              onMouseDown={props.onMouseDown}
              onTouchStart={props.onTouchStart}
              style={{
                ...props.style,
                height: "36px",
                display: "flex",
                width: "100%",
              }}
            >
              <div
                ref={props.ref}
                style={{
                  height: "5px",
                  width: "100%",
                  borderRadius: "4px",
                  background: getTrackBackground({
                    values: vals,
                    colors: [
                      disabled ? "rgba(0, 0, 0, 0.3)" : "#2684ff", // "#548BF4",
                      "#ccc",
                    ],
                    min: minValue,
                    max: maxValue,
                  }),
                  alignSelf: "center",
                }}
              >
                {children}

                <div
                  style={{
                    display: "inline-block",
                    width: "100%",
                    fontSize: "12px",
                    paddingTop: "13px",
                  }}
                >
                  <div style={{ float: "left" }}>{minValue}</div>
                  <div style={{ float: "right" }}>{maxValue}</div>
                </div>
              </div>
            </div>
          )}
          renderThumb={({ props, isDragged }) => (
            <div
              {...props}
              style={{
                ...props.style,
                height: "18px",
                width: "18px",
                border: "None",
                borderRadius: "4px",
                backgroundColor: "#FFF",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                boxShadow: "0px 2px 6px #AAA",
                outline: "none",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: "-24px",
                  color: "#fff",
                  fontWeight: "bold",
                  fontSize: "12px",
                  fontFamily: "Arial,Helvetica Neue,Helvetica,sans-serif",
                  padding: "2px",
                  borderRadius: "3px",
                  backgroundColor: disabled ? "rgba(0, 0, 0, 0.3)" : "#2684ff",
                }}
              >
                {vals[0]}
              </div>
              <div
                style={{
                  height: "12px",
                  width: "3px",
                  backgroundColor: isDragged ? "#2684ff" : "#CCC",
                }}
              />
            </div>
          )}
        />
      </div>
    </div>
  );
}

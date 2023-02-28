import React from "react";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "../slices/notebooksSlice";
import { Range, getTrackBackground } from "react-range";

type RangeProps = {
  widgetKey: string;
  label: string | null;
  value: [number, number] | null;
  min: number | null;
  max: number | null;
  step: number | null;
  vertical: boolean | null;
  disabled: boolean;
  runNb: () => void;
};

export default function RangeWidget({
  widgetKey,
  label,
  value,
  min,
  max,
  step,
  vertical,
  disabled,
  runNb,
}: RangeProps) {
  const dispatch = useDispatch();
  //const [updated, userInteraction] = useState(false);
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

  const values =
    value != null && value !== undefined && value.length === 2
      ? value
      : [minValue, maxValue];

  return (
    <div className="form-group mb-3">
      <label
        htmlFor={`range-slider-${label}`}
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
          values={values}
          step={stepValue}
          min={minValue}
          max={maxValue}
          onChange={(values) => {
            //userInteraction(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: values as [number, number],
              })
            );
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
                    values,
                    colors: [
                      "#ccc",
                      disabled ? "rgba(0, 0, 0, 0.3)" : "#2684ff",
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
          renderThumb={({ index, props, isDragged }) => (
            <div
              {...props}
              style={{
                ...props.style,
                height: "18px",
                width: "18px",
                border: "None !important",
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
                {values[index]}
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

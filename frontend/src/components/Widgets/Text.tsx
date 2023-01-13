import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { RUN_DELAY, setWidgetValue } from "../Notebooks/notebooksSlice";

type TextProps = {
  widgetKey: string;
  label: string | null;
  value: string | undefined;
  rows: number | null;
  disabled: boolean;
  runNb: () => void;
};

export default function TextWidget({
  widgetKey,
  label,
  value,
  rows,
  disabled,
  runNb,
}: TextProps) {
  const dispatch = useDispatch();
  let rowsValue: number = rows ? rows : 1;

  const sanitizeString = (input_string: string) => {
    return input_string.replace(/["'(){}[\]`^]/gim, "");
  };

  useEffect(() => {
    const timeOutId = setTimeout(() => {
      console.log(value);
      runNb();
    }, RUN_DELAY);
    return () => clearTimeout(timeOutId);
  }, [value]);

  return (
    <div className="form-group mb-3">
      <label htmlFor={`textarea-${label}`}>{label}</label>
      {rowsValue === 1 && (
        <input
          className="form-control"
          type="text"
          id={`text-${label}`}
          value={value ? value : ""}
          onChange={(e) => {
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
      {rowsValue > 1 && (
        <textarea
          className="form-control"
          id={`text-area-${label}`}
          rows={rowsValue}
          value={value ? value : ""}
          onChange={(e) => {
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
    </div>
  );
}

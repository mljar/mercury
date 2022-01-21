import React from "react";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "./widgetsSlice";

type TextProps = {
  widgetKey: string;
  label: string | null;
  value: string | undefined;
  rows: number | null;
  disabled: boolean;
};

export default function TextWidget({
  widgetKey,
  label,
  value,
  rows,
  disabled,
}: TextProps) {
  const dispatch = useDispatch();
  let rowsValue: number = (rows) ? rows : 1;

  const sanitizeString = (str: string) => {
    return str.replace(/[^a-z0-9\.,_\-\s]/gim, "");
  }

  return (
    <div className="form-group mb-3">
      <label htmlFor={`textarea-${label}`}>{label}</label>
      {rowsValue == 1 &&
        <input
          className="form-control"
          type="text"
          id={`text-${label}`}
          value={value}
          onChange={(e) => {
            dispatch(setWidgetValue({ key: widgetKey, value: sanitizeString(e.target.value) }))
          }}
          disabled={disabled} />
      }
      {rowsValue > 1 &&
        <textarea className="form-control"
          id={`text-area-${label}`}
          rows={rowsValue}
          value={value}
          onChange={(e) => {
            dispatch(setWidgetValue({ key: widgetKey, value: sanitizeString(e.target.value) }))
          }}
          disabled={disabled}
        />
      }
    </div>
  );
}

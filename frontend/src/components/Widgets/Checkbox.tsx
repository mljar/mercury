/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import { setWidgetValue } from "./widgetsSlice";

type CheckboxProps = {
  widgetKey: string;
  label: string | null;
  value: boolean | null;
  disabled: boolean;
};

export default function CheckboxWidget({
  widgetKey,
  label,
  value,
  disabled,
}: CheckboxProps) {
  const dispatch = useDispatch();
  return (
    <div className="form-group form-check form-switch mb-3">
      <input
        className="form-check-input"
        type="checkbox"
        id={`checkbox-${label}`}
        disabled={disabled}
        onChange={() => {
          dispatch(setWidgetValue({ key: widgetKey, value: !value }));
        }}
        checked={ value != null ? value : false}
      />
      <label className="form-check-label" htmlFor={`checkbox-${label}`}>
        {label}
      </label>
    </div>
  );
}

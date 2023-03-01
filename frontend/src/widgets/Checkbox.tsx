/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";

import { setWidgetValue } from "../slices/notebooksSlice";

type CheckboxProps = {
  widgetKey: string;
  label: string | null;
  value: boolean | null;
  disabled: boolean;
  runNb: () => void;
};

export default function CheckboxWidget({
  widgetKey,
  label,
  value,
  disabled,
  runNb,
}: CheckboxProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);

  useEffect(() => {
    if (updated) {
      //console.log("run from checkbox");
      runNb();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="form-group form-check form-switch mb-3">
      <input
        className="form-check-input"
        type="checkbox"
        id={`checkbox-${label}`}
        disabled={disabled}
        onChange={() => {
          userInteraction(true);
          dispatch(setWidgetValue({ key: widgetKey, value: !value }));
        }}
        checked={value != null ? value : false}
      />
      <label
        className="form-check-label"
        htmlFor={`checkbox-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
    </div>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useSearchParams } from "react-router-dom";

import {
  setUrlValuesUsed,
  setWidgetUrlValue,
  setWidgetValue,
} from "../slices/notebooksSlice";

type CheckboxProps = {
  widgetKey: string;
  label: string | null;
  value: boolean | null;
  disabled: boolean;
  hidden: boolean;
  runNb: () => void;
  url_key: string;
};

export default function CheckboxWidget({
  widgetKey,
  label,
  value,
  disabled,
  hidden,
  runNb,
  url_key,
}: CheckboxProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);

  const [searchParams] = useSearchParams();

  useEffect(() => {
    if (url_key !== undefined && url_key !== "") {
      const urlValue = searchParams.get(url_key)?.toLowerCase();

      if (
        !updated &&
        urlValue !== undefined &&
        (urlValue === "true" || urlValue === "false")
      ) {
        dispatch(
          setWidgetUrlValue({
            key: widgetKey,
            value: urlValue === "true",
          })
        );
        dispatch(setUrlValuesUsed(true));
      }
    }
  }, [dispatch, searchParams, updated, url_key, widgetKey]);

  useEffect(() => {
    if (updated) {
      runNb();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="form-group form-check form-switch mb-3"  style={{ display: hidden ? "none" : "" }}>
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

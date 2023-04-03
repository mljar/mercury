/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useSearchParams } from "react-router-dom";
import Select, { MultiValue } from "react-select";
import {
  setUrlValuesUsed,
  setWidgetUrlValue,
  setWidgetValue,
} from "../slices/notebooksSlice";

type SingleOption = { value: string; label: string };
type MultiOption = MultiValue<{ value: string; label: string } | undefined>;

export function isSingleOption(
  options: SingleOption | MultiOption
): options is SingleOption {
  return (options as SingleOption).value !== undefined;
}

type SelectProps = {
  widgetKey: string;
  label: string | null;
  value: string | string[] | null;
  choices: string[];
  multi: boolean | undefined;
  disabled: boolean;
  hidden: boolean;
  runNb: () => void;
  url_key: string;
};

export default function SelectWidget({
  widgetKey,
  label,
  value,
  choices,
  multi,
  disabled,
  hidden,
  runNb,
  url_key,
}: SelectProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);

  const selectStyles = {
    menu: (base: any) => ({
      ...base,
      zIndex: 100,
    }),
  };

  const [searchParams] = useSearchParams();
  useEffect(() => {
    if (url_key !== undefined && url_key !== "") {
      const urlValue = searchParams.get(url_key);
      if (!updated && urlValue !== undefined && urlValue !== null) {
        if (multi) {
          const arr = urlValue.split(",");
          if (arr) {
            dispatch(
              setWidgetUrlValue({
                key: widgetKey,
                value: arr.filter((a) => choices.includes(a)),
              })
            );
            dispatch(setUrlValuesUsed(true));
          }
        } else {
          if (choices.includes(urlValue)) {
            dispatch(
              setWidgetUrlValue({
                key: widgetKey,
                value: urlValue,
              })
            );
            dispatch(setUrlValuesUsed(true));
          }
        }
      }
    }
  }, [choices, dispatch, multi, searchParams, updated, url_key, widgetKey]);

  let selectedValue: SingleOption = { value: "", label: "" };
  let selectedValues: SingleOption[] = [{ value: "", label: "" }];

  let options: { value: string; label: string }[] = choices.map((choice) => {
    if (value && choice === value && !multi) {
      selectedValue = { value: choice, label: choice };
    }
    return { value: choice, label: choice };
  });

  if (multi) {
    selectedValues = [];
    choices.map((choice) => {
      if (value && value.includes(choice) && multi) {
        selectedValues.push({ value: choice, label: choice });
      }
      return { value: choice, label: choice };
    });
  }

  useEffect(() => {
    if (!updated) return;
    runNb();
    // const timeOutId = setTimeout(() => {
    //   // console.log("run from select");
    //   runNb();
    // }, RUN_DELAY_FAST);
    // return () => clearTimeout(timeOutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="form-group mb-3" style={{ display: hidden ? "none" : "" }}>
      <label
        htmlFor={`select-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
      <Select
        id={`select-${label}`}
        isDisabled={disabled}
        name={label ? label : "Select"}
        styles={selectStyles}
        value={multi ? selectedValues : selectedValue}
        options={options}
        isMulti={multi}
        onChange={(e) => {
          if (e) {
            userInteraction(true);
            if (isSingleOption(e)) {
              dispatch(setWidgetValue({ key: widgetKey, value: e.value }));
            } else {
              // console.log({ msg: "values", values: e.values() });
              const vs = Array.from(e.values()).filter(
                (i) => i !== undefined
              ) as { label: string; value: string }[];
              // console.log({
              //   key: widgetKey,
              // });
              dispatch(
                setWidgetValue({
                  key: widgetKey,
                  value: vs.map((i) => i.value) as string[],
                })
              );
            }
          }
        }}
      />
    </div>
  );
}

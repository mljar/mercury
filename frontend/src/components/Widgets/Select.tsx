/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch } from "react-redux";
import Select, { MultiValue } from "react-select";
import { setWidgetValue } from "./widgetsSlice";

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
};

export default function SelectWidget({
  widgetKey,
  label,
  value,
  choices,
  multi,
  disabled,
}: SelectProps) {
  const dispatch = useDispatch();

  const selectStyles = {
    menu: (base: any) => ({
      ...base,
      zIndex: 100,
    }),
  };

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

  return (
    <div className="form-group mb-3">
      <label htmlFor={`select-${label}`}>{label}</label>
      <Select
        id={`select-${label}`}
        isDisabled={disabled}
        name={label ? label : "Select"}
        styles={selectStyles}
        value={multi ? selectedValues : selectedValue}
        options={options}
        isMulti={multi}
        onChange={(e) => {
          console.log(e);

          if (e) {
            if (isSingleOption(e)) {
              console.log("single");
              dispatch(setWidgetValue({ key: widgetKey, value: e.value }));
            } else {
              console.log("multi");
              console.log({ msg: "values", values: e.values() });
              const vs = Array.from(e.values()).filter(
                (i) => i !== undefined
              ) as { label: string; value: string }[];
              console.log(vs);
              // console.log(vs.map((i) => i.value));
              console.log({
                key: widgetKey,
              });
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

/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import Select from "react-select";
import {
  getExecutionHistory,
  getHistoricTask,
  setHistoricTask,
} from "../tasks/tasksSlice";
import { setWidgetValue } from "./Widgets/widgetsSlice";
type SingleOption = { value: string; label: string };

type Props = {
  disabled: boolean;
};

export default function SelectExecutionHistory({ disabled }: Props) {
  const dispatch = useDispatch();
  const executionHistory = useSelector(getExecutionHistory);
  const historicTask = useSelector(getHistoricTask);

  console.log(executionHistory);
  if (executionHistory.length === 0) return <div></div>;

  const selectStyles = {
    menu: (base: any) => ({
      ...base,
      zIndex: 100,
    }),
  };

  let selectedValue: SingleOption = { value: "", label: "" };

  let count = 1;
  let options: { value: string; label: string }[] = executionHistory.map(
    (run) => {
      let choice = `Run ${count}`;
      count += 1;
      if (historicTask.id) {
        if (historicTask.id && historicTask.id === run.id) {
          selectedValue = { value: `${count - 2}`, label: choice };
        }
      } else {
        selectedValue = { value: `${count - 2}`, label: choice };
      }
      return { value: `${count - 2}`, label: choice };
    }
  );

  return (
    <div>
      <hr />

      <div className="form-group mb-3">
        <label htmlFor="select-execution-history">Execution history</label>
        <Select
          id="select-execution-history"
          isDisabled={disabled}
          name={"Select"}
          styles={selectStyles}
          value={selectedValue}
          options={options}
          isMulti={false}
          onChange={(e) => {
            if (e) {
              let historical = executionHistory[parseInt(e.value)];
              dispatch(setHistoricTask(historical));

              //console.log(historical.params);
              for (let [key, value] of Object.entries(
                JSON.parse(historical.params)
              )) {
                if (value !== null) {
                  //console.log({ key, value });
                  dispatch(setWidgetValue({ key, value }));
                }
              }
            }
          }}
        />
      </div>
    </div>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import Select from "react-select";
import {
  getCurrentTask,
  getExecutionHistory,
  getHistoricTask,
  getShowCurrent,
  //setHistoricTask,
} from "../slices/tasksSlice";
//import { setWidgetValue } from "./Widgets/widgetsSlice";
//import { setWidgetValue } from "../slices/notebooksSlice";

type SingleOption = { value: string; label: string };

type Props = {
  disabled: boolean;
  displayNb: (taskId: number) => void;
};

export default function SelectExecutionHistory({ disabled, displayNb }: Props) {
  const dispatch = useDispatch();
  const executionHistory = useSelector(getExecutionHistory);
  const historicTask = useSelector(getHistoricTask);
  const currentTask = useSelector(getCurrentTask);
  const showCurrent = useSelector(getShowCurrent);

  useEffect(() => {
    /*
    if (executionHistory.length > 0) {
      let lastHistoricTask = executionHistory[executionHistory.length - 1];

      if (!historicTask.id && currentTask.id === lastHistoricTask.id) {
        for (let [key, value] of Object.entries(
          JSON.parse(currentTask.params)
        )) {
          if (value !== null) {
            dispatch(setWidgetValue({ key, value }));
          }
        }
      }
    }*/
  }, [dispatch, executionHistory, historicTask, currentTask]);

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
      if (!showCurrent) {
        selectedValue = { value: `${count - 2}`, label: choice };
      }
      return { value: `${count - 2}`, label: choice };
    }
  );
  options.push({ value: "current", label: "Current" });
  if (showCurrent) {
    selectedValue = { value: "current", label: "Current" };
  }

  return (
    <div>
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
              if (e.value === "current") {
                displayNb(0);
              } else {
                let historical = executionHistory[parseInt(e.value)];
                console.log(historical.id);
                console.log(historical.params);

                displayNb(historical.id);

              }
              // let historical = executionHistory[parseInt(e.value)];
              // dispatch(setHistoricTask(historical));
              // for (let [key, value] of Object.entries(
              //   JSON.parse(historical.params)
              // )) {
              //   if (value !== null) {
              //     dispatch(setWidgetValue({ key, value }));
              //   }
              // }
            }
          }}
        />
      </div>
    </div>
  );
}

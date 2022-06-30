import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchCurrentTask, fetchExecutionHistory } from "../tasks/tasksSlice";

import {
  fetchNotebook,
  getSelectedNotebook,
  getWatchModeCounter,
} from "./Notebooks/notebooksSlice";

type Props = {
  notebookId: number;
};

function WatchMode({ notebookId }: Props) {
  const dispatch = useDispatch();
  const notebook = useSelector(getSelectedNotebook);
  const watchModeCounter = useSelector(getWatchModeCounter);

  useEffect(() => {
    if (
      notebook.state === "WATCH_READY" ||
      notebook.state === "WATCH_WAIT" ||
      notebook.state === "WATCH_ERROR"
    ) {
      setTimeout(() => {
        dispatch(fetchNotebook(notebookId, true));
        dispatch(fetchCurrentTask(notebookId));
        dispatch(fetchExecutionHistory(notebookId));
      }, 2000);
    }
  }, [dispatch, notebook, notebookId, watchModeCounter]);

  return <div></div>;
}

const WatchModeComponent = WatchMode;
export default WatchModeComponent;

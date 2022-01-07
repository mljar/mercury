import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { withRouter } from "react-router-dom";
import { useParams } from "react-router-dom";
import { fetchCurrentTask } from "../tasks/tasksSlice";

import {
  fetchNotebook,
  getSelectedNotebook,
  getWatchModeCounter,
} from "./Notebooks/notebooksSlice";

function WatchMode() {
  const dispatch = useDispatch();
  const { notebook_id } = useParams<{ notebook_id: string }>();
  const notebookId = Number(notebook_id);
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
      }, 2000);
    }
  }, [dispatch, notebook, notebookId, watchModeCounter]);

  return <div></div>;
}

const WatchModeComponent = withRouter(WatchMode);
export default WatchModeComponent;

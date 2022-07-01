import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchCurrentTask } from "../tasks/tasksSlice";

import { fetchNotebook, getSelectedNotebook } from "./Notebooks/notebooksSlice";

type Props = {
  notebookId: number;
};

export default function AutoRefresh({ notebookId }: Props) {
  const dispatch = useDispatch();
  const notebook = useSelector(getSelectedNotebook);

  useEffect(() => {
    setTimeout(() => {
      dispatch(fetchNotebook(notebookId, true));
      dispatch(fetchCurrentTask(notebookId));
    }, 60000); // every 1 minute
  }, [dispatch, notebookId, notebook]);

  return <div></div>;
}

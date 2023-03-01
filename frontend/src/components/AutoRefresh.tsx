import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchCurrentTask } from "../slices/tasksSlice";

import { fetchNotebook, getSelectedNotebook } from "../slices/notebooksSlice";

type Props = {
  siteId: number;
  notebookId: number;
};

export default function AutoRefresh({ siteId, notebookId }: Props) {
  const dispatch = useDispatch();
  const notebook = useSelector(getSelectedNotebook);

  useEffect(() => {
    setTimeout(() => {
      dispatch(fetchNotebook(siteId, notebookId, true));
      dispatch(fetchCurrentTask(notebookId));
    }, 60000); // every 1 minute
  }, [dispatch, siteId, notebookId, notebook]);

  return <div></div>;
}

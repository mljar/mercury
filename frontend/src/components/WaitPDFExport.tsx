import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "react-toastify";
import { fetchCurrentTask, getExportingToPDF, getExportToPDFCounter, getExportToPDFJobId, getPDF, increaseExportToPDFCounter, setExportingToPDF } from "../tasks/tasksSlice";

import { fetchNotebook, getSelectedNotebook } from "./Notebooks/notebooksSlice";


export default function WaitPDFExport() {
  const dispatch = useDispatch();
  const counter = useSelector(getExportToPDFCounter);
  const jobId = useSelector(getExportToPDFJobId);

  useEffect(() => {
    console.log("wait PDF export " + counter + ' ' + jobId);

    if(jobId === '') {
      return;
    } 
    if (counter < 8) {
      setTimeout(() => {
        console.log("set timeout " + counter);
        dispatch(increaseExportToPDFCounter());
        dispatch(getPDF(jobId));
        //dispatch(fetchNotebook(notebookId, true));
        //dispatch(fetchCurrentTask(notebookId));


      }, 1000); // every 1 second
    } else {
      dispatch(setExportingToPDF(false));
      toast.error("Problem with PDF export. Please try again later or ask your admin for help.", { autoClose: 6000 })

    }
  }, [dispatch, counter, jobId]);

  return <div></div>;
}

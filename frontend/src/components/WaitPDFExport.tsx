import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { toast } from "react-toastify";
import { getExportingToPDF, getExportToPDFCounter, getExportToPDFJobId, getPDF, stopPDFExport } from "../slices/tasksSlice";

export default function WaitPDFExport() {
  const dispatch = useDispatch();
  const counter = useSelector(getExportToPDFCounter);
  const jobId = useSelector(getExportToPDFJobId);
  const exportingPDF = useSelector(getExportingToPDF);

  useEffect(() => {
    if(jobId === '') {
      return;
    } 
    if(!exportingPDF) {
      return;
    }
    // raise error after 2 minutes of waiting ...
    if (counter < 120) {
      setTimeout(() => {
        dispatch(getPDF(jobId));
      }, 1000); // every 1 second
    } else {
      dispatch(stopPDFExport());
      toast.error("Problem with PDF export. Please try again later or ask your admin for help.", { autoClose: 6000 })
    }
  }, [dispatch, counter, jobId, exportingPDF]);

  return <div></div>;
}

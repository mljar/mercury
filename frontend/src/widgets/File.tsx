import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import axios, { AxiosProgressEvent } from "axios";

import { setWidgetValue } from "../slices/notebooksSlice";

import { FilePond, registerPlugin } from "react-filepond";
import FilePondPluginImageExifOrientation from "filepond-plugin-image-exif-orientation";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import FilePondPluginFileValidateSize from "filepond-plugin-file-validate-size";
import {
  deleteUserFileUploaded,
  fetchStorageType,
  getStorageType,
  userFileUploaded,
} from "../slices/appSlice";
import { toast } from "react-toastify";
import { getSiteId } from "../slices/sitesSlice";
import { getSessionId } from "../utils";

registerPlugin(
  FilePondPluginImageExifOrientation,
  FilePondPluginImagePreview,
  FilePondPluginFileValidateSize
);

type FileProps = {
  widgetKey: string;
  label: string | null;
  maxFileSize: string | null;
  disabled: boolean;
  hidden: boolean;
  value: string[];
  runNb: () => void;
};

export default function FileWidget({
  widgetKey,
  label,
  maxFileSize,
  disabled,
  hidden,
  value,
  runNb,
}: FileProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);
  const storageType = useSelector(getStorageType);
  const siteId = useSelector(getSiteId);
  const sessionId = useSelector(getSessionId);

  let fileSizeLimit = "100MB";
  if (maxFileSize) {
    fileSizeLimit = maxFileSize;
  }
  useEffect(() => {
    if (updated && value !== undefined && value.length === 2) {
      //console.log("run from file");
      runNb();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  useEffect(() => {
    dispatch(fetchStorageType());
  }, [dispatch]);

  const mediaServerActions = {
    url: `${axios.defaults.baseURL}/api/v1/fp`,
    process: "/process/",
    revert: async (
      uniqueFileId: any,
      load: () => void,
      error: (arg0: string) => void
    ) => {
      try {
        await axios.delete(`${axios.defaults.baseURL}/api/v1/fp/revert`, {
          data: uniqueFileId,
        });
        dispatch(setWidgetValue({ key: widgetKey, value: [] }));
        // Should call the load method when done, no parameters required
        load();
      } catch (e) {
        // Can call the error method if something is wrong, should exit after
        error("Problem with uploaded file removal");
      }
    },
  };
  const s3ServerActions = {
    process: (
      fieldName: string,
      file: { name: any; size: any },
      metadata: any,
      load: (arg0: any) => void,
      error: any,
      progress: (arg0: boolean, arg1: any, arg2: number) => void,
      abort: () => void
    ) => {
      const abortController = new AbortController();

      axios
        .get(
          `/api/v1/nb-file-put/${siteId}/${sessionId}/${file.name}/${file.size}`
        )
        .then((response) => {
          const { url } = response.data;

          let token = axios.defaults.headers.common["Authorization"];

          delete axios.defaults.headers.common["Authorization"];

          const config = {
            onUploadProgress: (progressEvent: AxiosProgressEvent) => {
              progress(
                progressEvent.total !== undefined,
                progressEvent.loaded,
                progressEvent.total as number
              );
            },
          };

          axios
            .put(url, file, {
              headers: {
                "Content-Type": "",
              },
              onUploadProgress: config.onUploadProgress,
              signal: abortController.signal,
            })
            .then((response) => {
              // file uploaded
              // set it as uploaded in filepond
              load(file.name);
              // save it in database
              if (siteId !== undefined) {
                dispatch(userFileUploaded(siteId, sessionId, file.name));
              }
            })
            .catch((error) => {
              toast.error("Error when uploading new files");
            });

          axios.defaults.headers.common["Authorization"] = token;
        })
        .catch((error) => {
          toast.error("Cant upload new files");
        });

      // Should expose an abort method so the request can be cancelled
      return {
        abort: () => {
          // This function is entered if the user has tapped the cancel button
          abortController.abort();
          // Let FilePond know the request has been cancelled
          abort();
        },
      };
    },
    revert: async (
      uniqueFileId: any,
      load: () => void,
      error: (arg0: string) => void
    ) => {
      try {
        if (siteId !== undefined) {
          dispatch(deleteUserFileUploaded(siteId, sessionId, uniqueFileId));
        }
        // Should call the load method when done, no parameters required
        load();
      } catch (e) {
        // Can call the error method if something is wrong, should exit after
        error("Problem with uploaded file removal");
      }
    },
  };

  return (
    <div className="form-group mb-3" style={{ display: hidden ? "none" : "" }}>
      <label
        htmlFor={`file-${label}`}
        style={{ color: disabled ? "#555" : "#212529" }}
      >
        {label}
      </label>
      <div>
        <FilePond
          disabled={disabled}
          maxFileSize={fileSizeLimit}
          onprocessfile={(error, file) => {
            userInteraction(true);
            dispatch(
              setWidgetValue({
                key: widgetKey,
                value: [file.filename, file.serverId],
              })
            );
          }}
          server={
            storageType === "media" ? mediaServerActions : s3ServerActions
          }
          labelIdle='Drag & Drop your file or <span class="filepond--label-action">Browse</span>'
        />
      </div>
    </div>
  );
}

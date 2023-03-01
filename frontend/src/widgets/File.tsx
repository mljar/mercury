import React, { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import { setWidgetValue } from "../slices/notebooksSlice";

import { FilePond, registerPlugin } from "react-filepond";
import FilePondPluginImageExifOrientation from "filepond-plugin-image-exif-orientation";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import FilePondPluginFileValidateSize from "filepond-plugin-file-validate-size";

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
  value: string[];
  runNb: () => void;
};

export default function FileWidget({
  widgetKey,
  label,
  maxFileSize,
  disabled,
  value,
  runNb,
}: FileProps) {
  const dispatch = useDispatch();
  const [updated, userInteraction] = useState(false);
  let fileSizeLimit = "100MB";
  if (maxFileSize) {
    fileSizeLimit = maxFileSize;
  }
  useEffect(() => {
    if (updated && value.length === 2) {
      //console.log("run from file");
      runNb();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="form-group mb-3">
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
          server={{
            url: `${axios.defaults.baseURL}/api/v1/fp`,
            process: "/process/",
            revert: async (uniqueFileId, load, error) => {
              try {
                await axios.delete(
                  `${axios.defaults.baseURL}/api/v1/fp/revert`,
                  {
                    data: uniqueFileId,
                  }
                );
                dispatch(setWidgetValue({ key: widgetKey, value: [] }));
                // Should call the load method when done, no parameters required
                load();
              } catch (e) {
                // Can call the error method if something is wrong, should exit after
                error("Problem with uploaded file removal");
              }
            },
          }}
          labelIdle='Drag & Drop your file or <span class="filepond--label-action">Browse</span>'
        />
      </div>
    </div>
  );
}

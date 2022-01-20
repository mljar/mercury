import React from "react";
import { useDispatch } from "react-redux";
import axios from "axios";
import { setWidgetValue } from "./widgetsSlice";

import { FilePond, registerPlugin } from 'react-filepond';
import FilePondPluginImageExifOrientation from 'filepond-plugin-image-exif-orientation';
import FilePondPluginImagePreview from 'filepond-plugin-image-preview';
import FilePondPluginFileValidateSize from 'filepond-plugin-file-validate-size';

registerPlugin(
  FilePondPluginImageExifOrientation,
  FilePondPluginImagePreview,
  FilePondPluginFileValidateSize,
);

type FileProps = {
  widgetKey: string;
  label: string | null;
  maxFileSize: string | null;
  disabled: boolean;
};

export default function FileWidget({
  widgetKey,
  label,
  maxFileSize,
  disabled,
}: FileProps) {
  const dispatch = useDispatch();
  let fileSizeLimit = "100MB";
  if(maxFileSize) {
    fileSizeLimit = maxFileSize;
  }
  return (
    <div className="form-group mb-3">
      <label htmlFor={`file-${label}`}>{label}</label>
      <div>
        <FilePond
          disabled={disabled}
          maxFileSize={fileSizeLimit}
          onprocessfile={(error, file) => {
            dispatch(setWidgetValue({ key: widgetKey, value: file.serverId }));
          }}
          server={{
            url: `${axios.defaults.baseURL}/api/v1/fp`,
            process: '/process/',
            revert: async (uniqueFileId, load, error) => {
              try {
                const response = await axios.delete(`${axios.defaults.baseURL}/api/v1/fp/revert`, {
                  data: uniqueFileId
                });
                dispatch(setWidgetValue({ key: widgetKey, value: [] }));
                // Should call the load method when done, no parameters required
                load();
              } catch (e) {
                // Can call the error method if something is wrong, should exit after
                error('Problem with uploaded file removal');
              }
            },
          }}
          labelIdle='Drag & Drop your file or <span class="filepond--label-action">Browse</span>'
        />
      </div>
    </div>
  );
}

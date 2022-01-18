import React, { useState } from "react";
import { useDispatch } from "react-redux";
// import { setWidgetValue } from "./widgetsSlice";

import { FilePond, registerPlugin } from 'react-filepond'
// import { FilePond as IFilePond, File as FilePondFile } from 'react-filepond'

import FilePondPluginImageExifOrientation from 'filepond-plugin-image-exif-orientation'
import FilePondPluginImagePreview from 'filepond-plugin-image-preview'

registerPlugin(FilePondPluginImageExifOrientation, FilePondPluginImagePreview)

type FileProps = {
  widgetKey: string;
  label: string | null;
  value: string | null;
  maxFileSize: string | null;
  disabled: boolean;
};

export default function FileWidget({
  widgetKey,
  label,
  value,
  maxFileSize,
  disabled,
}: FileProps) {
  const dispatch = useDispatch();
  const [files, setFiles] = useState([])

  return (
    <div className="form-group mb-3">
      <label htmlFor={`file-${label}`}>{label}</label>

      <div
        style={{
          paddingTop: "12px"
        }}
      >

        <FilePond
          files={files}
          onupdatefiles={(fileItems) => {console.log(fileItems[0].file)} }
          allowMultiple={false}
          // server="/api"
          // name="files" {/* sets the file input name, it's filepond by default */}
          labelIdle='Drag & Drop your file or <span class="filepond--label-action">Browse</span>'
          
        />
      </div>
    </div>
  );
}

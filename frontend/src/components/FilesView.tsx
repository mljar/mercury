/* eslint-disable jsx-a11y/anchor-is-valid */
import React from "react";
import axios from "axios";
import useWindowDimensions from "./WindowDimensions";

import BlockUi from "react-block-ui";


type FilesViewProps = {
};

export default function FilesView({
  
}:FilesViewProps) {
  const { height } = useWindowDimensions();

  return (
    <main
      className="col-md-9 ms-sm-auto col-lg-9"
      style={{ paddingTop: "0px", paddingRight: "0px", paddingLeft: "0px" }}
    >
    Files view
    </main>
  );
}

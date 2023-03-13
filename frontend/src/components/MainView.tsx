/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import axios from "axios";
import useWindowDimensions from "./WindowDimensions";

import BlockUi from "react-block-ui";
import { useDispatch, useSelector } from "react-redux";
import { getNotebookSrc, setNotebookSrc } from "../slices/wsSlice";

import InnerHTML from "dangerously-set-html-content";
import { getSelectedNotebook } from "../slices/notebooksSlice";

type MainViewProps = {
  appView: string;
  loadingState: string;
  notebookPath: string;
  waiting: boolean;
  errorMsg: string;
  watchMode: boolean;
  displayEmbed: boolean;
  username: string;
  slidesHash: string;
  columnsWidth: number;
  isPresentation: boolean;
  fullScreen: boolean;
};

export default function MainView({
  appView,
  loadingState,
  notebookPath,
  waiting,
  errorMsg,
  watchMode,
  displayEmbed,
  username,
  slidesHash,
  columnsWidth,
  isPresentation,
  fullScreen,
}: MainViewProps) {
  const { height } = useWindowDimensions();

  const iframeHeight = displayEmbed ? height - 10 : height - 58;
  const dispatch = useDispatch();
  let nb = useSelector(getSelectedNotebook);
  let notebookSrc = useSelector(getNotebookSrc);

  let showCode = false;
  if (nb !== undefined && nb.params !== undefined) {
    if (
      nb.params["show-code"] !== undefined &&
      nb.params["show-code"] !== null
    ) {
      showCode = nb.params["show-code"];
    }
  }

  if (notebookSrc !== "" && !isPresentation) {
    notebookSrc = "<script>init_mathjax();</script>" + notebookSrc;

    if (!showCode) {
      const hideCodeStyle = `<style type="text/css">
      .jp-mod-noOutputs {
          padding: 0px; 
      }
      .jp-mod-noInput {
        padding-top: 0px;
        padding-bottom: 0px;
      }
      </style>`;
      notebookSrc = hideCodeStyle + notebookSrc;
    }
  }

  if (notebookSrc !== "" && isPresentation && slidesHash !== "") {
    if (notebookSrc.indexOf("Reveal.slide(") === -1) {
      const splitted = slidesHash.split("/");
      let injectCode = "";
      if (splitted.length === 4) {
        injectCode = `Reveal.slide(${splitted[1]}, ${splitted[2]}, ${splitted[3]});`;
      } else if (splitted.length === 3) {
        injectCode = `Reveal.slide(${splitted[1]}, ${splitted[2]});`;
      } else if (splitted.length === 2) {
        injectCode = `Reveal.slide(${splitted[1]});`;
      }

      if (injectCode !== "") {
        notebookSrc = notebookSrc.replace(
          "setScrollingSlide);",
          `setScrollingSlide); try{ ${injectCode} } catch(error) {}`
        );
      }
    }
  }

  useEffect(() => {
    if (notebookPath !== undefined) {
      axios
        .get(`${notebookPath}${slidesHash}`)
        .then((response) => {
          let nbSrc = response.data;
          if (!isPresentation) {
            nbSrc = nbSrc.replace(/<head>[\s\S]*?<\/head>/, "");
            nbSrc = nbSrc.replace("<html>", "");
            nbSrc = nbSrc.replace("</html>", "");
            nbSrc = nbSrc.replace("<body", "<div");
            nbSrc = nbSrc.replace("</body>", "</div>");
            nbSrc = nbSrc.replace("<!DOCTYPE html>", "");
          }
          dispatch(setNotebookSrc(nbSrc));
        });
    }
  }, [dispatch, notebookPath, slidesHash, isPresentation]);

  let mainStyle = {
    paddingTop: "0px",
    paddingRight: "0px",
    paddingLeft: fullScreen ? "12px" : "0px",
    display: appView === "files" ? "none" : "block",
  };

  let divStyle = {};
  if (!fullScreen) {
    divStyle = { maxWidth: "1140px", margin: "auto" };
  }

  return (
    <main className={`ms-sm-auto col-${columnsWidth}`} style={mainStyle}>
      <BlockUi tag="div" blocking={waiting}>
        <div style={divStyle}>
          {loadingState === "loading" && !watchMode && (
            <p>Loading notebook. Please wait ...</p>
          )}
          {loadingState === "error" && (
            <p style={{ margin: "20px" }}>
              Problem while loading notebook. Please try again later or contact
              Mercury administrator.
            </p>
          )}

          {loadingState === "error" && username === "" && (
            <p style={{ margin: "20px" }}>
              <h5>Please log in to see the notebook</h5>
              <a href="/login" className="btn btn-primary btn-sm ">
                <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
              </a>
            </p>
          )}

          {errorMsg && (
            <div className="alert alert-danger mb-3" role="alert">
              <b>Notebook is executed with errors.</b>
              <p>{errorMsg}</p>
            </div>
          )}

          {errorMsg === "" &&
            loadingState !== "loading" &&
            isPresentation &&
            notebookSrc !== "" && (
              <iframe
                width="100%"
                height={iframeHeight}
                key={notebookPath}
                srcDoc={notebookSrc}
                title="display"
                id="main-iframe"
                onError={() => {
                  console.log("iframe error");
                }}
              ></iframe>
            )}

          {notebookSrc !== "" && !isPresentation && (
            <InnerHTML html={notebookSrc} />
          )}
        </div>
      </BlockUi>
    </main>
  );
}

/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import axios from "axios";
import useWindowDimensions from "./WindowDimensions";

import BlockUi from "react-block-ui";
import { useDispatch, useSelector } from "react-redux";
import { getNotebookSrc, setNotebookSrc } from "../websocket/wsSlice";

import InnerHTML from "dangerously-set-html-content";
import { getSelectedNotebook } from "./Notebooks/notebooksSlice";

type MainViewProps = {
  loadingState: string;
  notebookPath: string;
  waiting: boolean;
  errorMsg: string;
  watchMode: boolean;
  displayEmbed: boolean;
  isPro: boolean;
  username: string;
  slidesHash: string;
  columnsWidth: number;
  isPresentation: boolean;
};

export default function MainView({
  loadingState,
  notebookPath,
  waiting,
  errorMsg,
  watchMode,
  displayEmbed,
  isPro,
  username,
  slidesHash,
  columnsWidth,
  isPresentation,
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
        .get(`${axios.defaults.baseURL}${notebookPath}${slidesHash}`)
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

  return (
    <main
      className={`ms-sm-auto col-lg-${columnsWidth}`}
      style={{
        paddingTop: "0px",
        paddingRight: "0px",
        paddingLeft: "0px",
        //display: "none",
      }}
    >
      <BlockUi tag="div" blocking={waiting}>
        <div>
          {loadingState === "loading" && !watchMode && (
            <p>Loading notebook. Please wait ...</p>
          )}
          {loadingState === "error" && !isPro && (
            <p style={{ margin: "20px" }}>
              Problem while loading notebook. Please try again later or contact
              Mercury administrator.
            </p>
          )}

          {loadingState === "error" && isPro && username === "" && (
            <p style={{ margin: "20px" }}>
              <h5>Please log in to see the notebook</h5>
              <a href="/login" className="btn btn-primary btn-sm ">
                <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
              </a>
            </p>
          )}

          {loadingState === "error" && isPro && username !== "" && (
            <p style={{ margin: "20px" }}>
              Problem while loading notebook. Please try again later or contact
              Mercury administrator.
            </p>
          )}
          {/* {waiting && (
          <div className="alert alert-primary mb-3" role="alert">
            Notebook is executed. Default notebook is presented below. New
            results will be loaded after execution.{" "}
            <i className="fa fa-coffee" aria-hidden="true"></i> Please wait ...
          </div>
        )} */}
          {errorMsg && (
            <div className="alert alert-danger mb-3" role="alert">
              <b>Notebook is executed with errors.</b>
              <p>{errorMsg}</p>
            </div>
          )}

          {/* {errorMsg === "" &&
            loadingState !== "loading" &&
            isPresentation && (
              <iframe
                width="100%"
                height={iframeHeight}
                key={notebookPath}
                src={`${axios.defaults.baseURL}${notebookPath}${slidesHash}`}
                title="display"
                id="main-iframe"
              ></iframe>
            )}  */}

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

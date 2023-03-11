import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import "./App.css";
import NavBar from "../components/NavBar";
import SideBar from "../components/SideBar";
import MainView from "../components/MainView";

import {
  fetchNotebookWithSlug,
  getLoadingStateSelected,
  getSelectedNotebook,
  getSlidesHash,
  // getWatchModeCounter,
} from "../slices/notebooksSlice";
import {
  //fetchCurrentTask,
  //fetchExecutionHistory,
  getCurrentTask,
  getExportingToPDF,
  getHistoricTask,
  getPreviousTask,
  //ITask,
  //setPreviousTask,
} from "../slices/tasksSlice";
import { isOutputFilesWidget, IWidget } from "../widgets/Types";
import {
  fetchWorkerOutputFiles,
  getOutputFiles,
  getOutputFilesState,
  getShowSideBar,
  getView,
  setShowSideBar,
} from "../slices/appSlice";
import FilesView from "../components/FilesView";
import { getToken, getUsername } from "../slices/authSlice";
import MadeWithDiv from "../components/MadeWithDiv";
import RestAPIView from "../components/RestAPIView";
import BlockUi from "react-block-ui";
import WaitPDFExport from "../components/WaitPDFExport";
import { getWorkerId, getWorkerState, WorkerState } from "../slices/wsSlice";
import { getSiteId, isPublic } from "../slices/sitesSlice";

type AppProps = {
  isSingleApp: boolean;
  notebookSlug: string;
  displayEmbed: boolean;
};

function App({ isSingleApp, notebookSlug, displayEmbed }: AppProps) {
  const dispatch = useDispatch();
  const notebook = useSelector(getSelectedNotebook);
  const loadingState = useSelector(getLoadingStateSelected);
  const task = useSelector(getCurrentTask);
  const historicTask = useSelector(getHistoricTask);
  const previousTask = useSelector(getPreviousTask);
  const appView = useSelector(getView);
  const outputFiles = useSelector(getOutputFiles);
  const outputFilesState = useSelector(getOutputFilesState);
  const username = useSelector(getUsername);
  const token = useSelector(getToken);
  const slidesHash = useSelector(getSlidesHash);
  const showSideBar = useSelector(getShowSideBar);
  const exportingToPDF = useSelector(getExportingToPDF);
  const workerId = useSelector(getWorkerId);
  const workerState = useSelector(getWorkerState);
  const siteId = useSelector(getSiteId);
  const isSitePublic = useSelector(isPublic);

  const pleaseWait = () => {
    if (notebook?.params?.static_notebook) {
      return false;
    }
    return workerState !== WorkerState.Running;
  };

  const isWatchMode = () => {
    return (
      notebook.state === "WATCH_READY" ||
      notebook.state === "WATCH_WAIT" ||
      notebook.state === "WATCH_ERROR"
    );
  };

  useEffect(() => {
    if (siteId !== undefined) {
      dispatch(fetchNotebookWithSlug(siteId, notebookSlug));
    }
  }, [dispatch, siteId, notebookSlug, token]);

  useEffect(() => {
    if (
      appView === "files" &&
      notebook?.params?.version === "2" &&
      workerId !== undefined &&
      notebook.id !== undefined
    ) {
      dispatch(fetchWorkerOutputFiles(workerId, notebook.id));
    }
  }, [dispatch, appView, notebook, workerId]);

  let notebookPath = notebook.default_view_path;
  if (task.state && task.state === "DONE" && task.result) {
    notebookPath = task.result;
  }
  let errorMsg = "";
  if (task.state && task.result && task.state === "ERROR") {
    errorMsg = task.result;
  }

  // set historic task to display if available
  if (
    historicTask.state &&
    historicTask.state === "DONE" &&
    historicTask.result
  ) {
    notebookPath = historicTask.result;
  }
  if (
    historicTask.state &&
    historicTask.result &&
    historicTask.state === "ERROR"
  ) {
    errorMsg = historicTask.result;
  }

  // if we have previous task to show, just show it
  if (
    notebookPath === notebook.default_view_path &&
    previousTask.state &&
    previousTask.state === "DONE" &&
    previousTask.result
  ) {
    notebookPath = previousTask.result;
  }

  const areOutputFilesAvailable = (
    widgetsParams: Record<string, IWidget>
  ): boolean => {
    if (widgetsParams) {
      for (let [, widgetParams] of Object.entries(widgetsParams)) {
        if (isOutputFilesWidget(widgetParams)) {
          return true;
        }
      }
    }
    return false;
  };

  let showRestApi = false;
  if (notebook.output && notebook.output.toLowerCase().startsWith("rest")) {
    showRestApi = true;
  }

  const isFullScreen = () => {
    if (notebook !== undefined && notebook !== null) {
      return notebook?.params?.full_screen !== undefined &&
        notebook?.params?.full_screen !== null
        ? notebook.params.full_screen
        : true;
    }
    return true;
  };

  const doAllowDownload = () => {
    if (notebook !== undefined && notebook !== null) {
      return notebook?.params?.allow_download !== undefined &&
        notebook?.params?.allow_download !== null
        ? notebook.params.allow_download
        : true;
    }
    return true;
  };

  return (
    <div className="App">
      {!displayEmbed && (
        <NavBar isSitePublic={isSitePublic} username={username} />
      )}
      <BlockUi
        blocking={exportingToPDF}
        message="Exporting to PDF. Please wait ..."
      >
        {exportingToPDF && <WaitPDFExport />}
        <div className="container-fluid">
          <div className="row">
            {/* {notebook.schedule !== undefined && notebook.schedule !== "" && (
              <AutoRefresh notebookId={notebookId} />
            )} */}

            {showSideBar && (
              <SideBar
                notebookTitle={notebook.title}
                notebookId={notebook.id}
                notebookSchedule={notebook.schedule}
                taskCreatedAt={task.created_at}
                loadingState={loadingState}
                waiting={pleaseWait()} // {waitForTask()}
                widgetsParams={notebook?.params?.params}
                watchMode={isWatchMode()}
                notebookPath={notebookPath}
                displayEmbed={displayEmbed}
                showFiles={areOutputFilesAvailable(notebook?.params?.params)}
                isPresentation={
                  notebook.output !== undefined && notebook.output === "slides"
                }
                notebookParseErrors={notebook.errors}
                continuousUpdate={notebook?.params?.continuous_update}
                staticNotebook={notebook?.params?.static_notebook}
                allowDownload={doAllowDownload()}
              />
            )}

            {!showSideBar && (
              <div>
                <button
                  className="btn btn-sm  btn-outline-primary"
                  type="button"
                  style={{
                    position: "absolute",
                    top: displayEmbed ? "5px" : "50px",
                    left: "5px",
                    zIndex: "100",
                  }}
                  onClick={() => dispatch(setShowSideBar(true))}
                  data-toggle="tooltip"
                  data-placement="right"
                  title="Show sidebar"
                >
                  <i className="fa fa-chevron-right" aria-hidden="true" />
                </button>
              </div>
            )}

            {showRestApi && (
              <RestAPIView
                slug={notebook.slug}
                widgetsParams={notebook?.params?.params}
                notebookPath={notebookPath}
                columnsWidth={showSideBar ? 9 : 12}
                taskSessionId={task.session_id}
              />
            )}

            <MainView
              appView={appView}
              loadingState={loadingState}
              notebookPath={notebookPath}
              errorMsg={errorMsg}
              waiting={pleaseWait()} // {waitForTask()}
              watchMode={isWatchMode()}
              displayEmbed={displayEmbed}
              username={username}
              slidesHash={slidesHash}
              columnsWidth={showSideBar ? 9 : 12}
              isPresentation={
                notebook.output !== undefined && notebook.output === "slides"
              }
              fullScreen={isFullScreen()}
            />

            {appView === "files" && (
              <FilesView
                files={outputFiles}
                filesState={outputFilesState}
                waiting={pleaseWait()} // {waitForTask()}
              />
            )}
          </div>
        </div>
      </BlockUi>
      {displayEmbed && <MadeWithDiv />}
    </div>
  );
}

const AppView = App;
export default AppView;

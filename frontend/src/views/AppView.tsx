import React, { useContext, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import "./App.css";
import NavBar from "../components/NavBar";
import SideBar from "../components/SideBar";
import MainView from "../components/MainView";

import {
  fetchNotebook,
  getLoadingStateSelected,
  getSelectedNotebook,
  getSlidesHash,
  // getWatchModeCounter,
} from "../components/Notebooks/notebooksSlice";
import {
  fetchCurrentTask,
  fetchExecutionHistory,
  getCurrentTask,
  getExportingToPDF,
  getHistoricTask,
  getPreviousTask,
  ITask,
  setPreviousTask,
} from "../tasks/tasksSlice";
import WatchModeComponent from "../components/WatchMode";
import { isOutputFilesWidget, IWidget } from "../components/Widgets/Types";
import {
  fetchOutputFiles,
  getOutputFiles,
  getOutputFilesState,
  getShowSideBar,
  getView,
  setShowSideBar,
} from "./appSlice";
import FilesView from "../components/FilesView";
import { getToken, getUsername } from "../components/authSlice";
import { getIsPro } from "../components/versionSlice";
import MadeWithDiv from "../components/MadeWithDiv";
import RestAPIView from "../components/RestAPIView";
import AutoRefresh from "../components/AutoRefresh";
import BlockUi from "react-block-ui";
import WaitPDFExport from "../components/WaitPDFExport";


type AppProps = {
  isSingleApp: boolean;
  notebookId: number;
  displayEmbed: boolean;
};

function App({ isSingleApp, notebookId, displayEmbed }: AppProps) {
  const dispatch = useDispatch();
  const notebook = useSelector(getSelectedNotebook);
  const loadingState = useSelector(getLoadingStateSelected);
  const task = useSelector(getCurrentTask);
  const historicTask = useSelector(getHistoricTask);
  const previousTask = useSelector(getPreviousTask);
  const appView = useSelector(getView);
  const outputFiles = useSelector(getOutputFiles);
  const outputFilesState = useSelector(getOutputFilesState);
  const isPro = useSelector(getIsPro);
  const username = useSelector(getUsername);
  const token = useSelector(getToken);
  const slidesHash = useSelector(getSlidesHash);
  const showSideBar = useSelector(getShowSideBar);
  const exportingToPDF = useSelector(getExportingToPDF);

  const waitForTask = () => {
    if (task.state && task.state === "CREATED") return true;
    if (task.state && task.state === "RECEIVED") return true;
    return false;
  };

  const isWatchMode = () => {
    return (
      notebook.state === "WATCH_READY" ||
      notebook.state === "WATCH_WAIT" ||
      notebook.state === "WATCH_ERROR"
    );
  };

  useEffect(() => {
    dispatch(fetchNotebook(notebookId));
    dispatch(fetchCurrentTask(notebookId));
    dispatch(fetchExecutionHistory(notebookId));
    dispatch(setPreviousTask({} as ITask));
  }, [dispatch, notebookId, token]);

  useEffect(() => {
    if (waitForTask()) {
      setTimeout(() => {
        dispatch(fetchCurrentTask(notebookId));
        dispatch(fetchExecutionHistory(notebookId, false));
      }, 1000);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch, task, notebookId]);

  // useEffect(() => {
  //   if (isWatchMode()) {
  //     setTimeout(() => {
  //       dispatch(fetchNotebook(notebookId));
  //     }, 2000);
  //   }
  //   // eslint-disable-next-line react-hooks/exhaustive-deps
  // }, [dispatch, notebook, watchModeCounter]);

  useEffect(() => {
    if (
      appView === "files" &&
      task.id &&
      task.state &&
      task.state === "DONE" &&
      task.result
    ) {
      dispatch(fetchOutputFiles(task.id));
    }
  }, [dispatch, appView, task.id, task.state, task.result]);

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

  const areOutputFilesAvailable = (widgetsParams: IWidget[]): boolean => {
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

  return (
    <div className="App">
      {!displayEmbed && <NavBar isPro={isPro} username={username} />}
      <BlockUi
        blocking={exportingToPDF}
        message="Exporting to PDF. Please wait ..."
      >
        {exportingToPDF && <WaitPDFExport />}
        <div className="container-fluid">
          <div className="row">
            <WatchModeComponent notebookId={notebookId} />

            {notebook.schedule !== undefined && notebook.schedule !== "" && (
              <AutoRefresh notebookId={notebookId} />
            )}

            {showSideBar && (
              <SideBar
                notebookTitle={notebook.title}
                notebookId={notebookId}
                notebookSchedule={notebook.schedule}
                taskCreatedAt={task.created_at}
                loadingState={loadingState}
                waiting={waitForTask()}
                widgetsParams={notebook?.params?.params}
                watchMode={isWatchMode()}
                notebookPath={notebookPath}
                displayEmbed={displayEmbed}
                showFiles={areOutputFilesAvailable(notebook?.params?.params)}
                isPresentation={
                  notebook.output !== undefined && notebook.output === "slides"
                }
                notebookParseErrors={notebook.errors}
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
            {appView === "app" && (
              <MainView
                loadingState={loadingState}
                notebookPath={notebookPath}
                errorMsg={errorMsg}
                waiting={waitForTask()}
                watchMode={isWatchMode()}
                displayEmbed={displayEmbed}
                isPro={isPro}
                username={username}
                slidesHash={slidesHash}
                columnsWidth={showSideBar ? 9 : 12}
              />
            )}
            {appView === "files" && (
              <FilesView
                files={outputFiles}
                filesState={outputFilesState}
                waiting={waitForTask()}
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

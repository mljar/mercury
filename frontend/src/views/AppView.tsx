import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import "./App.css";
import NavBar from "../components/NavBar";
import SideBar from "../components/SideBar";
import MainView from "../components/MainView";
import { withRouter } from "react-router-dom";
import { useParams } from "react-router-dom";

import {
  fetchNotebook,
  getLoadingStateSelected,
  getSelectedNotebook,
  // getWatchModeCounter,
} from "../components/Notebooks/notebooksSlice";
import { fetchCurrentTask, getCurrentTask } from "../tasks/tasksSlice";
import WatchModeComponent from "../components/WatchMode";

function App() {
  const dispatch = useDispatch();
  const { notebook_id } = useParams<{ notebook_id: string }>();
  const notebookId = Number(notebook_id);
  const notebook = useSelector(getSelectedNotebook);
  const loadingState = useSelector(getLoadingStateSelected);
  // const watchModeCounter = useSelector(getWatchModeCounter);
  const task = useSelector(getCurrentTask);


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
  }, [dispatch, notebookId]);

  useEffect(() => {
    if (waitForTask()) {
      setTimeout(() => {
        dispatch(fetchCurrentTask(notebookId));
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

  let notebookPath = notebook.default_view_path;
  if (task.state && task.state === "DONE" && task.result) {
    notebookPath = task.result;
  }
  let errorMsg = "";
  if (task.state && task.result && task.state === "ERROR") {
    errorMsg = task.result;
  }

  return (
    <div className="App">
      <NavBar />
      <div className="container-fluid">
        <div className="row">
          <WatchModeComponent />
          <SideBar
            notebookTitle={notebook.title}
            notebookId={Number(notebook_id)}
            loadingState={loadingState}
            waiting={waitForTask()}
            widgetsParams={notebook?.params?.params}
            watchMode={isWatchMode()}
            notebookPath={notebookPath}
          />

          <MainView
            loadingState={loadingState}
            notebookPath={notebookPath}
            errorMsg={errorMsg}
            waiting={waitForTask()}
            watchMode={isWatchMode()}
          />
        </div>
      </div>
    </div>
  );
}

const AppView = withRouter(App);
export default AppView;

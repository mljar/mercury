/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import { withRouter } from "react-router-dom";
import HomeNavBar from "../components/HomeNavBar";
import Footer from "../components/Footer";
import {
  fetchNotebooks,
  getLoadingState,
  getNotebooks,
} from "../components/Notebooks/notebooksSlice";
import { fetchWelcome, getIsPro, getWelcome } from "../components/versionSlice";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import emoji from "remark-emoji";
import rehypeRaw from "rehype-raw";
import { getToken, getUsername } from "../components/authSlice";

export default withRouter(function HomeView() {
  const dispatch = useDispatch();
  const notebooks = useSelector(getNotebooks);
  const loadingState = useSelector(getLoadingState);
  const welcome = useSelector(getWelcome);
  const isPro = useSelector(getIsPro);
  const username = useSelector(getUsername);
  const token = useSelector(getToken);

  useEffect(() => {
    dispatch(fetchNotebooks());
    dispatch(fetchWelcome());
    // fetchNotebooks depends on token
    // if token is set then private notebooks are returned
  }, [dispatch, token]);

  const firstLetters = (text: string | null, count: number): string => {
    if (text !== null && text !== undefined) {
      return text.slice(0, count) + (text.length > count ? " ..." : "");
    }
    return "";
  };

  const notebookItems = notebooks.map((notebook, index) => {
    return (
      <div
        className="col-md-4"
        style={{ paddingBottom: "20px" }}
        key={`notebook-${notebook.id}}`}
      >
        <div className="card">
          <div
            style={{
              height: "200px",
              width: "100%",
              padding: "1px",
              overflow: "hidden",
            }}
          >
            <iframe
              className="thumbnailIframe"
              width="200%"
              height={800}
              src={`${axios.defaults.baseURL}${notebook.default_view_path}`}
              title="display"
              scrolling="no"
            ></iframe>
          </div>
          <a
            href={`/app/${notebook.slug}`}
            style={{ textDecoration: "none", color: "black" }}
            className="title-card"
          >
            <div
              className="card-body"
              style={{
                borderTop: "1px solid rgba(0,0,0,0.1)",
                height: "110px",
              }}
            >
              <h5 className="card-title">{firstLetters(notebook.title, 40)}</h5>

              <p className="card-text">
                {firstLetters(notebook.params.description, 100)}
              </p>

              {/* <a href={`/app/${notebook.id}`} className="btn btn-primary">
              Open <i className="fa fa-arrow-right" aria-hidden="true"></i>
            </a> */}
            </div>
          </a>
        </div>
      </div>
    );
  });

  document.body.style.backgroundColor = "white";

  return (
    <div className="App">
      <HomeNavBar isPro={isPro} username={username} />
      <div className="container" style={{ paddingBottom: "50px" }}>
        {welcome === "" && (
          <h1 style={{ padding: "30px", textAlign: "center" }}>Welcome!</h1>
        )}
        {welcome !== "" && (
          <div style={{ paddingTop: "20px", paddingBottom: "10px" }}>
            <ReactMarkdown
              rehypePlugins={[remarkGfm, rehypeHighlight, emoji, rehypeRaw]}
            >
              {welcome}
            </ReactMarkdown>
          </div>
        )}

        <div className="row">
          {loadingState === "loading" && (
            <p>Loading notebooks. Please wait ...</p>
          )}

          {loadingState === "loaded" && isPro && notebooks.length === 0 && (
            <div>
              <div className="alert alert-success" role="alert">
                <h5>
                  <i className="fa fa-key" aria-hidden="true"></i> You are using
                  Pro version
                </h5>
                <p>
                  There are no public notebooks shared. Please login with your
                  credentials to check private notebooks.
                </p>

                <a href="/login" className="btn btn-primary btn-sm ">
                  <i className="fa fa-sign-in" aria-hidden="true"></i> Log in
                </a>
              </div>
            </div>
          )}
          {loadingState === "loaded" && notebooks.length === 0 && (
            <div>
              <p>
                There are no notebooks available. Please add notebook to Mercury
                server.
              </p>

              <p>
                Command to watch notebook development in Mercury (with automatic
                refresh):
              </p>
              <div className="alert alert-primary" role="alert">
                <pre style={{ margin: "0px" }}>
                  mercury watch {"<path_to_notebook>"}
                </pre>
              </div>

              <p>Command to add notebook to your Mercury server:</p>
              <div className="alert alert-primary" role="alert">
                <pre style={{ margin: "0px" }}>
                  mercury add {"<path_to_notebook>"}
                </pre>
              </div>
            </div>
          )}
          {loadingState === "error" && (
            <p>
              Problem while loading notebooks. Please try again later or contact
              Mercury administrator.
            </p>
          )}
          {notebookItems}
        </div>
      </div>
      <Footer />
    </div>
  );
});

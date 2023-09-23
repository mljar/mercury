/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import HomeNavBar from "../components/HomeNavBar";
import Footer from "../components/Footer";
import {
  // fetchNbIframes,
  fetchNotebooks,
  getLoadingState,
  // getNbIframes,
  getNotebooks,
} from "../slices/notebooksSlice";
import { fetchWelcome, getWelcome } from "../slices/versionSlice";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import emoji from "remark-emoji";
import rehypeRaw from "rehype-raw";
import { getToken, getUsername } from "../slices/authSlice";
import {
  getFooterText,
  getLogoFilename,
  getNavbarColor,
  getSiteId,
  getSiteWelcome,
  isPublic,
} from "../slices/sitesSlice";
import axios from "axios";

import DefaultLogoSrc from "../components/DefaultLogo";
import { Link } from "react-router-dom";

export default function HomeView() {
  const dispatch = useDispatch();
  const notebooks = useSelector(getNotebooks);
  const loadingState = useSelector(getLoadingState);
  const welcome = useSelector(getWelcome);
  const username = useSelector(getUsername);
  const token = useSelector(getToken);
  const [showButton, setShowButton] = useState("");
  const siteId = useSelector(getSiteId);
  const isSitePublic = useSelector(isPublic);
  const siteWelcome = useSelector(getSiteWelcome);
  const [logoSrc, setLogoSrc] = useState("loading");
  const logoFilename = useSelector(getLogoFilename);
  const navbarColor = useSelector(getNavbarColor);
  const footerText = useSelector(getFooterText);

  useEffect(() => {
    console.log({logoFilename})
    if (siteId !== undefined) {
      if (logoFilename === "") {
        setLogoSrc(DefaultLogoSrc);
      } else {
        axios
          .get(`/api/v1/get-style/${siteId}/${logoFilename}`)
          .then((response) => {
            const { url } = response.data;
            setLogoSrc(url);
          });
      }
    }
  }, [dispatch, logoFilename, siteId]);

  useEffect(() => {
    if (siteId !== undefined) {
      dispatch(fetchNotebooks(siteId));
      if (siteWelcome === undefined || siteWelcome === "") {
        dispatch(fetchWelcome(siteId));
      }
    }
    // fetchNotebooks depends on token
    // if token is set then private notebooks are returned
  }, [dispatch, siteId, token, siteWelcome]);

  const firstLetters = (text: string | null, count: number): string => {
    if (text !== null && text !== undefined) {
      return text.slice(0, count) + (text.length > count ? " ..." : "");
    }
    return "";
  };

  const notebookItems = notebooks.map((notebook, index) => {
    let nbPath = notebook.default_view_path;

    if (window.location.origin.startsWith("https")) {
      nbPath = nbPath.replace("http://", "https://");
    }

    if (window.location.origin === "http://localhost:3000") {
      if (nbPath.startsWith("/media")) {
        nbPath = "https://127.0.0.1:8000" + nbPath;
      }
    }

    // if (window.location.origin !== "http://localhost:3000") {
    //   if (nbPath.startsWith("https://127.0.0.1:8000")) {
    //     nbPath = nbPath.replace(
    //       "https://127.0.0.1:8000",
    //       window.location.origin
    //     );
    //   }
    //   if (nbPath.startsWith("http://127.0.0.1:8000")) {
    //     nbPath = nbPath.replace(
    //       "http://127.0.0.1:8000",
    //       window.location.origin
    //     );
    //   }
    // }

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
              src={nbPath}
              title="display"
              scrolling="no"
            ></iframe>

            {/* <img
              alt="some alt" 
              
              width="100%"
              src={`${notebook.default_view_path.replace(".html", ".png")}`}
            ></img> */}
          </div>
          <Link
            to={`/app/${notebook.slug}`}
            style={{ textDecoration: "none", color: "black" }}
            className="title-card"
            onMouseEnter={() => {
              setShowButton(notebook.slug);
            }}
            onMouseLeave={() => {
              setShowButton("");
            }}
            reloadDocument
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
            </div>
            {showButton === notebook.slug && (
              <button
                className="btn btn-outline-primary"
                type="button"
                style={{
                  zIndex: "101",
                  border: "none",
                  margin: "5px",
                  position: "absolute",
                  right: "0px",
                  bottom: "0px",
                }}
                data-toggle="tooltip"
                data-placement="right"
                title={`Open ${notebook.title}`}
              >
                <i className="fa fa-chevron-right" aria-hidden="true" />
              </button>
            )}
          </Link>
        </div>
      </div>
    );
  });

  document.body.style.backgroundColor = "white";

  let welcomeMd = siteWelcome;
  if (welcomeMd === undefined || welcomeMd === "") {
    welcomeMd = welcome;
  }

  return (
    <div className="App">
      <HomeNavBar
        isSitePublic={isSitePublic}
        username={username}
        logoSrc={logoSrc}
        navbarColor={navbarColor}
      />
      <div className="container" style={{ paddingBottom: "50px" }}>
        {welcomeMd === "" && (
          <h1 style={{ padding: "30px", textAlign: "center" }}>Welcome!</h1>
        )}
        {welcomeMd !== "" && (
          <div style={{ paddingTop: "20px", paddingBottom: "10px" }}>
            <ReactMarkdown
              rehypePlugins={[remarkGfm, rehypeHighlight, emoji, rehypeRaw]}
            >
              {welcomeMd}
            </ReactMarkdown>
          </div>
        )}

        <div className="row">
          {loadingState === "loading" && (
            <p>Loading notebooks. Please wait ...</p>
          )}

          {loadingState === "loaded" && notebooks.length === 0 && (
            <div>
              <p>There are no notebooks available.</p>
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
      <Footer footerText={footerText} />
    </div>
  );
}

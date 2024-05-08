/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getUsername,
} from "../slices/authSlice";
import Footer from "../components/Footer";
import HomeNavBar from "../components/HomeNavBar";
import {
  getFooterText,
  getLogoFilename,
  getNavbarColor,
  getSiteId,
  isPublic,
} from "../slices/sitesSlice";
import axios from "axios";

import DefaultLogoSrc from "../components/DefaultLogo";
import { fetchNotebooks, getNotebooks } from "../slices/notebooksSlice";
import { isSelectWidget, isSliderWidget } from "../widgets/Types";

export default function OpenAPIView() {
  const dispatch = useDispatch();

  const [logoSrc, setLogoSrc] = useState("loading");

  const username = useSelector(getUsername);

  const isSitePublic = useSelector(isPublic);
  const logoFilename = useSelector(getLogoFilename);
  const siteId = useSelector(getSiteId);
  const navbarColor = useSelector(getNavbarColor);
  const footerText = useSelector(getFooterText);
  const notebooks = useSelector(getNotebooks);

  useEffect(() => {
    if (siteId !== undefined) {
      dispatch(fetchNotebooks(siteId));
    }
  }, [dispatch, siteId]);

  document.body.style.backgroundColor = "white";

  useEffect(() => {
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

  const responses = `, "responses": {
    "200": {
        "description": "OK",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                      "state": {
                        "type": "string"
                      },
                      "message": {
                        "type": "string"
                      },
                      "result": {
                        "type": "string"
                      }
                  }
                }
            }
        }
    },
    "202": {
      "description": "Request accepted",
      "content": {
          "application/json": {
              "schema": {
                  "type": "object",
                  "properties": {
                    "state": {
                      "type": "string"
                    },
                    "message": {
                      "type": "string"
                    }
                }
              }
          }
      }
  }  
}`;

  const notebookApis = notebooks.map((nb) => {
    const endpoint = `/api/v1/${siteId}/run/${nb.slug}`;

    const parameters = Object.entries(nb.params.params)
      .map((p) => {
        const w = p[1];

        if (isSliderWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${w.label}",
            "required": false,
            "schema": {
                "type": "integer"
                }
            }`;
          }
        } else if (isSelectWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${w.label}",
            "required": false,
            "schema": {
                "type": "string"
                }
            }`;
          }
        }
        return ``;
      })
      .filter((s) => s !== "");

    let desc = `"${endpoint}": {
      "post": {
          "operationId": "Execute notebook ${nb.slug}",
          "description": "${nb.params.description}"
       `;
    if (parameters.length > 0) {
      desc += `, "parameters": [`;
      desc += parameters.join(",");
      desc += `]`;
    }
    desc += responses;
    desc += `}}`;
    return desc;
  });
  
  const schema = `{
    "openapi": "3.0",
    "info": {
        "description": "Execute Python notebook and get JSON response",
        "title": "Mercury OpenAPI",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "${axios.defaults.baseURL}"
        }
    ],
    "paths": {
        ${notebookApis.join(",")}
    }
}`;

  return (
    <div className="App">
      <HomeNavBar
        isSitePublic={isSitePublic}
        username={username}
        logoSrc={logoSrc}
        navbarColor={navbarColor}
      />

      <div className="container">
        <div className="mx-auto" style={{ width: "700px" }}>
          <div className="row" style={{ marginTop: "40px" }}>
            <h2>OpenAPI schema</h2>
          </div>
          <pre
            style={{
              border: "1px solid #eee",
              borderRadius: "10px",
              padding: "10px",
              marginBottom: "80px",
            }}
          >
            {JSON.stringify(JSON.parse(schema), null, 2)}
          </pre>
        </div>
      </div>

      <Footer footerText={footerText} />
    </div>
  );
}

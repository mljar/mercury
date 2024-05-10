/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { getSiteId } from "../slices/sitesSlice";
import axios from "axios";

import { fetchNotebooks, getNotebooks } from "../slices/notebooksSlice";
import {
  isCheckboxWidget,
  isNumericWidget,
  isRangeWidget,
  isSelectWidget,
  isSliderWidget,
  isTextWidget,
} from "../widgets/Types";

export default function OpenAPIView() {
  const dispatch = useDispatch();
  const siteId = useSelector(getSiteId);
  const notebooks = useSelector(getNotebooks);

  useEffect(() => {
    if (siteId !== undefined) {
      dispatch(fetchNotebooks(siteId));
    }
  }, [dispatch, siteId]);

  const createTaskResponse = `, "responses": {
    "201": {
        "description": "Request accepted for preprocessing, please check the processing state of the request using task_id",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
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
            "description": "${w.label}, value should be from range ${w.min} to ${w.max}",
            "required": false,
            "schema": {
                "type": "number"
                }
            }`;
          }
        } else if (isSelectWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${
              w.label
            }, value should be from list [${w.choices.join(",")}]",
            "required": false,
            "schema": {
                "type": "string"
                }
            }`;
          }
        } else if (isCheckboxWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${w.label}",
            "required": false,
            "schema": {
                "type": "boolean"
                }
            }`;
          }
        } else if (isNumericWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${w.label}, value should be in range  ${w.min} to ${w.max}",
            "required": false,
            "schema": {
                "type": "number"
                }
            }`;
          }
        } else if (isRangeWidget(w)) {
          if (w.url_key !== "") {
            return `{
            "name": "${w.url_key}",
            "in": "body",
            "description": "${w.label}, parameter should be string with comma separated values, for example 3,5, allowed range is ${w.min} to ${w.max}",
            "required": false,
            "schema": {
                "type": "string"
                }
            }`;
          }
        } else if (isTextWidget(w)) {
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
    desc += createTaskResponse;
    desc += `
        }
      }
    `;
    return desc;
  });

  const getTaskResponse = `"responses": {
    "200": {
        "description": "Request processing completed successfully",
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
      "description": "Request is still processing, please retry in 3 seconds",
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

  const getTask = `, "/api/v1/get/{task_id}": {
    "get" : {
      "operationId": "Get state and result of processed request",
      "description": "Use this endpoint to check if request processing state and result",
      "parameters": [
        {
          "name": "task_id",
          "in": "path",
          "description": "task_id of your request",
          "required": true,
          "schema": {
            "type": "string"
          }
        }
      ],
      ${getTaskResponse}
      }
    }`;

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
        ${getTask}
  }
}`;

  return <pre>{schema}</pre>;
}

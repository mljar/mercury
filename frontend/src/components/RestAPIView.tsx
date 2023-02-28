/* eslint-disable jsx-a11y/anchor-is-valid */
import React, { useEffect, useState } from "react";
import axios from "axios";
import { IWidget } from "../widgets/Types";
import { useSelector } from "react-redux";
import { getWidgetsValues } from "../slices/notebooksSlice";

type Props = {
  slug: string;
  widgetsParams: Record<string, IWidget>;  
  notebookPath: string;
  columnsWidth: number;
  taskSessionId: string | undefined;
};

export default function RestAPIView({
  slug,
  widgetsParams,
  notebookPath,
  columnsWidth,
  taskSessionId,
}: Props) {
  const [response, setResponse] = useState(
    JSON.stringify({ msg: "Example output" })
  );
  const widgetsValues = useSelector(getWidgetsValues);

  let examplePostData = {} as Record<
    string,
    | string
    | number
    | null
    | undefined
    | boolean
    | [number, number]
    | string[]
    | unknown
  >;
  for (let [key, widgetParams] of Object.entries(widgetsParams)) {
    if (widgetParams.input) {
      examplePostData[key] = widgetsValues[key];
    }
  }

  async function fetchResponse() {
    try {
      const { data } = await axios.get(`get/${taskSessionId}`);
      setResponse(JSON.stringify(data));
    } catch (error) {}
  }

  useEffect(() => {
    if (taskSessionId) {
      fetchResponse();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskSessionId, notebookPath]);

  let sessionId = "id-with-some-random-string";
  if (taskSessionId) {
    sessionId = taskSessionId;
  }

  let postRequest = `curl -X POST -H "Content-Type: application/json" -d '${JSON.stringify(
    examplePostData
  )}' ${axios.defaults.baseURL}/run/${slug}`;
  return (
    <div
      className={`ms-sm-auto col-lg-${columnsWidth}`}
      style={{
        border: "none",
        paddingTop: "0px",
        paddingRight: "0px",
        paddingLeft: "0px",
        padding: "10px",
      }}
    >
      <h4>Notebook as REST API</h4>
      <p>
        This notebook can be executed as REST API. Please see the examples below
        on how to access the notebook.
      </p>

      <div className="alert alert-secondary" role="alert">
        <h5>POST request to execute the notebook</h5>
        <textarea
          disabled
          style={{ width: "100%" }}
          rows={3}
          value={postRequest}
        ></textarea>
        The above request should return a JSON with `id`. The `id` should be
        used in the GET request to fetch the result.
        <br />
        Example response:
        <pre>{`{"id": "${sessionId}"}`}</pre>
      </div>
      <div className="alert alert-secondary" role="alert">
        <h5>GET request to get execution result in JSON</h5>
        <textarea
          disabled
          style={{ width: "100%" }}
          rows={1}
          value={`curl ${axios.defaults.baseURL}/get/${sessionId}`}
        ></textarea>
      </div>

      <div className="alert alert-primary" role="alert">
        <h5>Response</h5>
        <pre>{response}</pre>
      </div>
    </div>
  );
}

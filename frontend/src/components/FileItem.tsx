import axios from "axios";
import fileDownload from "js-file-download";

type Props = {
  fname: string;
  downloadLink: string;
  firstItem: boolean;
  lastItem: boolean;
};

export default function FileItem({
  fname,
  downloadLink,
  firstItem,
  lastItem,
}: Props) {
  const handleDownload = (url: string, filename: string) => {
    let token = axios.defaults.headers.common["Authorization"];

    if (url.includes("s3.amazonaws.com")) {
      // we cant do requests to s3 with auth token
      // we need to remove auth token before request
      delete axios.defaults.headers.common["Authorization"];
    }

    axios
      .get(url, {
        responseType: "blob",
      })
      .then((res) => {
        fileDownload(res.data, filename);
      });

    if (url.includes("s3.amazonaws.com")) {
      // after request we set token back
      axios.defaults.headers.common["Authorization"] = token;
    }
  };

  return (
    <div
      style={{
        border: "1px solid #ddd",
        marginBottom: "-1px",
        padding: "13px",
        borderTopRightRadius: firstItem ? "7px" : "0px",
        borderTopLeftRadius: firstItem ? "7px" : "0px",
        borderBottomRightRadius: lastItem ? "7px" : "0px",
        borderBottomLeftRadius: lastItem ? "7px" : "0px",
      }}
    >
      <i
        className="fa fa-file-text-o"
        aria-hidden="true"
        style={{ paddingRight: "5px" }}
      ></i>{" "}
      {fname}
      <div style={{ float: "right", margin: "-4px" }}>
        <button
          style={{ float: "right" }}
          type="button"
          className="btn btn-outline-primary btn-sm"
          onClick={() => handleDownload(downloadLink, fname!)}
        >
          <i className="fa fa-download" aria-hidden="true"></i> Download
        </button>
      </div>
    </div>
  );
}

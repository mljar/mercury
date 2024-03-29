import { v4 as uuidv4 } from 'uuid';
import axios from "axios";
import fileDownload from "js-file-download";
import { toast } from 'react-toastify';

export const getSessionId = (forceReload: boolean = false): string => {
    var sessionId = sessionStorage.getItem("sessionId");
    if (sessionId === null || forceReload === true) {
        sessionId = uuidv4();
        sessionStorage.setItem("sessionId", sessionId);
    }
    return sessionId;
}

export const setAxiosAuthToken = (token: string | null) => {
    if (typeof token !== "undefined" && token) {
        // Apply for every request
        axios.defaults.headers.common["Authorization"] = "Token " + token;
    } else {
        // Delete auth header
        delete axios.defaults.headers.common["Authorization"];
    }
};

export const handleDownload = (url: string, filename: string) => {
    axios
        .get(url, {
            responseType: "blob",
        })
        .then((res) => {
            fileDownload(res.data, filename);
        })
        .catch((err) => {
            toast.error(`Error during ${filename} download`)
        })
};
import { v4 as uuidv4 } from 'uuid';

export const getSessionId = () => {
    var sessionId = sessionStorage.getItem("sessionId");
    if (sessionId == null) {
        sessionId = uuidv4();
        sessionStorage.setItem("sessionId", sessionId);
    }
    return sessionId;
}
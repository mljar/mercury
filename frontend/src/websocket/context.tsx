import React, { createContext } from "react";

const WebSocketContext = createContext(undefined as any);

export { WebSocketContext };

export default function WebSocketProvider({
  children,
}: {
  children: JSX.Element;
}) {
  console.log("WebSocketProvider");

  let ws = null;

  const sendMessage = (payload: string) => {
    console.log("sendMessage", payload);
  };
   
  ws = {
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

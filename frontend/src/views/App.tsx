import { useParams, withRouter } from "react-router-dom";
import AppView from "./AppView";

import WebSocketProvider from "../websocket/Provider";

function MyApp() {
  const { notebook_id } = useParams<{ notebook_id: string }>();
  const notebookId = Number(notebook_id);

  const { embed } = useParams<{ embed: string }>();
  const displayEmbed = !!(embed && embed === "embed");

  return (
    <WebSocketProvider>
      <AppView
        isSingleApp={false}
        notebookId={notebookId}
        displayEmbed={displayEmbed}
      />
    </WebSocketProvider>
  );
}

const App = withRouter(MyApp);
export default App;

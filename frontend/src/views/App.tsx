import { useParams, withRouter } from "react-router-dom";
import AppView from "./AppView";

import WebSocketProvider from "../websocket/Provider";

function MyApp() {
  const { slug } = useParams<{ slug: string }>();
  const { embed } = useParams<{ embed: string }>();
  const displayEmbed = !!(embed && embed === "embed");

  return (
    <WebSocketProvider>
      <AppView
        isSingleApp={false}
        notebookSlug={slug}
        displayEmbed={displayEmbed}
      />
    </WebSocketProvider>
  );
}

const App = withRouter(MyApp);
export default App;

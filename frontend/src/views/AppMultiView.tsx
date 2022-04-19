import { useParams, withRouter } from "react-router-dom";
import AppView from "./AppView";

function App() {
  const { notebook_id } = useParams<{ notebook_id: string }>();
  const notebookId = Number(notebook_id);

  const { embed } = useParams<{ embed: string }>();
  const displayEmbed = !!(embed && embed === "embed");

  return (
    <AppView
      isSingleApp={false}
      notebookId={notebookId}
      displayEmbed={displayEmbed}
    />
  );
}

const AppMultiView = withRouter(App);
export default AppMultiView;
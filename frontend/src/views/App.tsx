import { useParams } from "react-router-dom";
import AppView from "./AppView";

export default function MyApp() {
  const { slug } = useParams<{ slug: string }>();
  const { embed } = useParams<{ embed: string }>();
  const displayEmbed = !!(embed && embed === "embed");

  return (
    <AppView
      isSingleApp={false}
      notebookSlug={slug as string}
      displayEmbed={displayEmbed}
    />
  );
}

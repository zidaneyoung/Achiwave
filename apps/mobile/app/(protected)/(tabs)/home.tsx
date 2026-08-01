import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function HomeTabRoute() {
  return (
    <RootDestinationScreen
      description="Your focused starting point for daily progress. Stage 6 will connect authoritative campaign and quest data."
      detailHref={PROTECTED_ROUTES.detail("home")}
      detailLabel="Open Home details"
      eyebrow="Daily command"
      title="Welcome to Achiwave"
    />
  );
}

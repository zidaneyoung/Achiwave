import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function ProgressTabRoute() {
  return (
    <RootDestinationScreen
      description="Confirmed XP, levels, streaks, and achievements will appear here only after later backend-authoritative stages."
      detailHref={PROTECTED_ROUTES.detail("progress")}
      detailLabel="Open Progress details"
      eyebrow="Authoritative results"
      title="Progress"
    />
  );
}

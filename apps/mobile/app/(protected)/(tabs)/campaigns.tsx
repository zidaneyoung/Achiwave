import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function CampaignsTabRoute() {
  return (
    <RootDestinationScreen
      description="Campaign management begins in Stage 6. This destination establishes navigation only and does not create local campaign data."
      detailHref={PROTECTED_ROUTES.detail("campaigns")}
      detailLabel="Open Campaigns details"
      eyebrow="Objectives"
      title="Campaigns"
    />
  );
}

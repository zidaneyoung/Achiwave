import { useRouter } from "expo-router";

import { AppButton } from "../../../src/components/AppButton";
import { RootDestinationScreen } from "../../../src/navigation/RootDestinationScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";

export default function CampaignsTabRoute() {
  const router = useRouter();
  return (
    <RootDestinationScreen
      description="Create and organize objectives using server-authoritative campaign data."
      eyebrow="Objectives"
      title="Campaigns"
    >
      <AppButton
        icon="plus"
        label="Create campaign"
        onPress={() => router.push(PROTECTED_ROUTES.campaignCreate)}
      />
    </RootDestinationScreen>
  );
}

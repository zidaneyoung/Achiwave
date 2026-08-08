import { useRef, useState } from "react";
import { AccessibilityInfo, StyleSheet, View } from "react-native";
import { Stack, useRouter } from "expo-router";

import { campaignApi, CampaignRequestError } from "../../../src/campaigns/api";
import { validateCampaignForm } from "../../../src/campaigns/form";
import { AppButton } from "../../../src/components/AppButton";
import { ErrorState } from "../../../src/components/ErrorState";
import { AppTextField } from "../../../src/components/FormControls";
import {
  campaignFormSnapshotsEqual,
  createCampaignFormSnapshot,
} from "../../../src/forms/snapshots";
import { KeyboardAwareScreen } from "../../../src/platform/KeyboardAwareScreen";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import {
  DirtyFormDialog,
  useDirtyFormGuard,
} from "../../../src/navigation/useDirtyFormGuard";
import { AppText } from "../../../src/theme/AppText";
import { spacing } from "../../../src/theme/tokens";

interface SubmissionIdentity {
  payloadKey: string;
  mutationId: string;
}

export default function CreateCampaignRoute() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [attempted, setAttempted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const submissionIdentity = useRef<SubmissionIdentity | null>(null);
  const baseline = useRef(createCampaignFormSnapshot("", "")).current;
  const currentSnapshot = createCampaignFormSnapshot(title, description);
  const guard = useDirtyFormGuard(
    !campaignFormSnapshotsEqual(baseline, currentSnapshot),
  );
  const validation = validateCampaignForm(title, description);

  async function submit() {
    setAttempted(true);
    setSubmissionError(null);
    if (validation.titleError || validation.descriptionError || submitting) return;
    const payloadKey = JSON.stringify({
      description: validation.description,
      title: validation.title,
    });
    if (submissionIdentity.current?.payloadKey !== payloadKey) {
      submissionIdentity.current = {
        payloadKey,
        mutationId: campaignApi.createMutationId(),
      };
    }
    setSubmitting(true);
    try {
      await campaignApi.create({
        title: validation.title,
        description: validation.description,
        clientMutationId: submissionIdentity.current.mutationId,
      });
      AccessibilityInfo.announceForAccessibility("Campaign created.");
      guard.completeNavigation(() => router.replace(PROTECTED_ROUTES.campaigns));
    } catch (error) {
      const message =
        error instanceof CampaignRequestError
          ? error.message
          : "The campaign could not be saved. Try again.";
      setSubmissionError(message);
      AccessibilityInfo.announceForAccessibility(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAwareScreen contentContainerStyle={styles.content}>
      <Stack.Screen options={{ headerBackButtonMenuEnabled: false, title: "Create campaign" }} />
      <AppText accessibilityRole="header" variant="heading1">
        Create campaign
      </AppText>
      <AppText tone="muted">
        Start with an objective. Quests can be added later.
      </AppText>
      <View style={styles.fields}>
        <AppTextField
          autoCapitalize="sentences"
          autoCorrect
          editable={!submitting}
          errorText={attempted ? validation.titleError ?? undefined : undefined}
          label="Title"
          maxLength={121}
          onChangeText={setTitle}
          required
          returnKeyType="next"
          value={title}
        />
        <AppTextField
          autoCapitalize="sentences"
          autoCorrect
          editable={!submitting}
          errorText={attempted ? validation.descriptionError ?? undefined : undefined}
          helperText="Optional planning context."
          label="Description"
          maxLength={4_001}
          multiline
          numberOfLines={5}
          onChangeText={setDescription}
          textAlignVertical="top"
          value={description}
        />
      </View>
      {submissionError ? (
        <View style={styles.error}>
          <ErrorState kind="inline" />
          <AppText accessibilityLiveRegion="assertive" tone="error">
            {submissionError}
          </AppText>
        </View>
      ) : null}
      <AppButton
        label="Create campaign"
        loading={submitting}
        onPress={() => void submit()}
      />
      <DirtyFormDialog busy={submitting} guard={guard} />
    </KeyboardAwareScreen>
  );
}

const styles = StyleSheet.create({
  content: {
    flexGrow: 1,
    gap: spacing.sm,
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  fields: { gap: spacing.md, marginVertical: spacing.sm },
  error: { gap: spacing.xs },
});

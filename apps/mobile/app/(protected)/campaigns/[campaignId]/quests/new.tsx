import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";

import { campaignApi, CampaignRequestError } from "../../../../../src/campaigns/api";
import { invalidateCachedCampaign } from "../../../../../src/campaigns/cache";
import type { CampaignDetail } from "../../../../../src/campaigns/types";
import { useAuthentication } from "../../../../../src/auth/AuthContext";
import { AppButton } from "../../../../../src/components/AppButton";
import { ErrorState } from "../../../../../src/components/ErrorState";
import { AppTextField } from "../../../../../src/components/FormControls";
import { LoadingSkeleton } from "../../../../../src/components/LoadingSkeleton";
import { PROTECTED_ROUTES } from "../../../../../src/navigation/routes";
import { KeyboardAwareScreen } from "../../../../../src/platform/KeyboardAwareScreen";
import { questApi, QuestRequestError } from "../../../../../src/quests/api";
import { validateOneTimeQuestForm } from "../../../../../src/quests/form";
import { AppText } from "../../../../../src/theme/AppText";
import { spacing } from "../../../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

function QuestForm({ campaign, ownerId }: { campaign: CampaignDetail; ownerId: string }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [reward, setReward] = useState("0");
  const [attempted, setAttempted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const submissionIdentity = useRef<{ payload: string; mutationId: string } | null>(null);
  const validation = validateOneTimeQuestForm(title, reward, description);

  async function submit() {
    setAttempted(true);
    setSubmissionError(null);
    if (validation.titleError || validation.rewardError || validation.descriptionError || submitting) return;
    const payload = JSON.stringify({ title: validation.title, description: validation.description, rewardXp: validation.rewardXp, version: campaign.recordVersion });
    if (submissionIdentity.current?.payload !== payload) {
      submissionIdentity.current = { payload, mutationId: questApi.createMutationId() };
    }
    setSubmitting(true);
    try {
      await questApi.createOneTime({
        campaignId: campaign.id,
        campaignRecordVersion: campaign.recordVersion,
        title: validation.title,
        description: validation.description,
        rewardXp: validation.rewardXp,
        clientMutationId: submissionIdentity.current.mutationId,
      });
      invalidateCachedCampaign(ownerId, campaign.id);
      AccessibilityInfo.announceForAccessibility("Quest created.");
      router.replace(PROTECTED_ROUTES.campaignDetail(campaign.id));
    } catch (error) {
      const message = error instanceof QuestRequestError ? error.message : "The quest could not be created.";
      setSubmissionError(message);
      AccessibilityInfo.announceForAccessibility(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <AppText accessibilityRole="header" variant="heading1">Create one-time quest</AppText>
      <AppText tone="muted">Add one action to {campaign.title}. Completion remains a later-stage action.</AppText>
      <View style={styles.fields}>
        <AppTextField
          editable={!submitting}
          errorText={attempted ? validation.titleError ?? undefined : undefined}
          label="Title"
          maxLength={121}
          onChangeText={setTitle}
          required
          value={title}
        />
        <AppTextField
          editable={!submitting}
          errorText={attempted ? validation.descriptionError ?? undefined : undefined}
          helperText="Optional planning context. It is not completion evidence."
          label="Description"
          maxLength={4_001}
          multiline
          numberOfLines={5}
          onChangeText={setDescription}
          textAlignVertical="top"
          value={description}
        />
        <AppTextField
          editable={!submitting}
          errorText={attempted ? validation.rewardError ?? undefined : undefined}
          helperText="Configured reward only. XP is not awarded until a future accepted completion."
          keyboardType="number-pad"
          label="XP reward"
          onChangeText={setReward}
          required
          value={reward}
        />
      </View>
      {submissionError ? (
        <View style={styles.error}>
          <ErrorState kind="inline" />
          <AppText accessibilityLiveRegion="assertive" tone="error">{submissionError}</AppText>
        </View>
      ) : null}
      <AppButton label="Create quest" loading={submitting} onPress={() => void submit()} />
    </>
  );
}

export default function CreateQuestRoute() {
  const params = useLocalSearchParams<{ campaignId?: string | string[] }>();
  const campaignId = typeof params.campaignId === "string" && UUID.test(params.campaignId) ? params.campaignId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sequence = useRef(0);

  const load = useCallback(async () => {
    if (!campaignId || !ownerId) return;
    const request = ++sequence.current;
    setError(null);
    try {
      const result = await campaignApi.get(campaignId);
      if (request !== sequence.current) return;
      if (result.status !== "active") {
        setError("Only active campaigns can accept new quests.");
        return;
      }
      setCampaign(result);
    } catch (caught) {
      if (request !== sequence.current) return;
      setError(caught instanceof CampaignRequestError ? caught.message : "The campaign could not be loaded.");
    }
  }, [campaignId, ownerId]);

  useFocusEffect(useCallback(() => {
    void load();
    return () => { sequence.current += 1; };
  }, [load]));

  if (!ownerId) return null;
  return (
    <KeyboardAwareScreen contentContainerStyle={styles.content}>
      <Stack.Screen options={{ title: "Create quest" }} />
      {!campaign && !error && campaignId ? <LoadingSkeleton label="Loading quest form" layout="card" /> : null}
      {(!campaign && error) || !campaignId ? (
        <View style={styles.error}>
          <ErrorState kind="fullScreen" onRetry={campaignId ? () => void load() : undefined} />
          <AppText accessibilityLiveRegion="assertive" tone="error">{campaignId ? error : "This campaign link is invalid."}</AppText>
        </View>
      ) : null}
      {campaign ? <QuestForm campaign={campaign} ownerId={ownerId} /> : null}
    </KeyboardAwareScreen>
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.xxl },
  fields: { gap: spacing.md, marginVertical: spacing.sm },
  error: { gap: spacing.xs },
});

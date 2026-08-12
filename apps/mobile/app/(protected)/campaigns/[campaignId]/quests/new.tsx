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
import {
  createQuestFormSnapshot,
  questFormSnapshotsEqual,
} from "../../../../../src/forms/snapshots";
import { PROTECTED_ROUTES } from "../../../../../src/navigation/routes";
import {
  DirtyFormDialog,
  useDirtyFormGuard,
} from "../../../../../src/navigation/useDirtyFormGuard";
import { KeyboardAwareScreen } from "../../../../../src/platform/KeyboardAwareScreen";
import { preferenceApi } from "../../../../../src/preferences/api";
import { questApi, QuestRequestError } from "../../../../../src/quests/api";
import { validateOneTimeQuestForm } from "../../../../../src/quests/form";
import { QuestDueDateTimeField } from "../../../../../src/quests/QuestDueDateTimeField";
import { QuestOptionSelector } from "../../../../../src/quests/QuestOptionSelector";
import type {
  QuestAuthoringOptions,
  QuestCategory,
  QuestDifficulty,
} from "../../../../../src/quests/types";
import { AppText } from "../../../../../src/theme/AppText";
import { spacing } from "../../../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

function QuestForm({
  campaign,
  ownerId,
  timezoneName,
  options,
}: {
  campaign: CampaignDetail;
  ownerId: string;
  timezoneName: string | null;
  options: QuestAuthoringOptions;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<QuestCategory | null>(null);
  const [difficulty, setDifficulty] = useState<QuestDifficulty>("medium");
  const [reward, setReward] = useState("0");
  const [due, setDue] = useState("");
  const [attempted, setAttempted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const submissionIdentity = useRef<{ payload: string; mutationId: string } | null>(null);
  const baseline = useRef(createQuestFormSnapshot({
    title: "",
    description: "",
    category: null,
    difficulty: "medium",
    reward: "0",
    committedDue: "",
  })).current;
  const currentSnapshot = createQuestFormSnapshot({
    title,
    description,
    category,
    difficulty,
    reward,
    committedDue: due,
  });
  const guard = useDirtyFormGuard(
    !questFormSnapshotsEqual(baseline, currentSnapshot),
  );
  const validation = validateOneTimeQuestForm(
    title,
    reward,
    description,
    due,
    options.rewardXpValues,
  );
  const rewardOptions = options.rewardXpValues.map((value) => ({
    value: String(value),
    label: `${value} XP`,
  }));

  async function submit() {
    setAttempted(true);
    setSubmissionError(null);
    if (validation.titleError || validation.rewardError || validation.descriptionError || validation.dueError || submitting) return;
    const payload = JSON.stringify({ title: validation.title, description: validation.description, category, difficulty, rewardXp: validation.rewardXp, dueLocalDateTime: validation.dueLocalDateTime, version: campaign.recordVersion });
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
        category,
        difficulty,
        rewardXp: validation.rewardXp,
        dueLocalDateTime: validation.dueLocalDateTime,
        clientMutationId: submissionIdentity.current.mutationId,
      });
      invalidateCachedCampaign(ownerId, campaign.id);
      AccessibilityInfo.announceForAccessibility("Quest created.");
      guard.completeNavigation(() =>
        router.replace(PROTECTED_ROUTES.campaignDetail(campaign.id)),
      );
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
      <AppText tone="muted">
        Add one action to {campaign.title}. The server recalculates campaign status after creation.
      </AppText>
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
        <QuestOptionSelector
          disabled={submitting}
          helperText="Optional planning label. Uncategorized quests remain valid."
          label="Category"
          nullableLabel="Uncategorized"
          onChange={(value) => setCategory(value as QuestCategory | null)}
          options={options.categories}
          value={category}
        />
        <QuestOptionSelector
          disabled={submitting}
          helperText="Planning effort only. Difficulty does not determine XP."
          label="Difficulty"
          onChange={(value) => {
            if (value !== null) setDifficulty(value as QuestDifficulty);
          }}
          options={options.difficulties}
          required
          value={difficulty}
        />
        <QuestOptionSelector
          disabled={submitting}
          errorText={attempted ? validation.rewardError ?? undefined : undefined}
          helperText="Configured reward only. XP is not awarded until a future accepted completion."
          label="XP reward"
          onChange={(value) => {
            if (value !== null) setReward(value);
          }}
          options={rewardOptions}
          required
          value={reward}
        />
        <QuestDueDateTimeField
          disabled={submitting}
          errorText={attempted ? validation.dueError ?? undefined : undefined}
          onChange={setDue}
          timeZoneName={timezoneName}
          value={due}
        />
      </View>
      {submissionError ? (
        <View style={styles.error}>
          <ErrorState kind="inline" />
          <AppText accessibilityLiveRegion="assertive" tone="error">{submissionError}</AppText>
        </View>
      ) : null}
      <AppButton label="Create quest" loading={submitting} onPress={() => void submit()} />
      <DirtyFormDialog busy={submitting} guard={guard} />
    </>
  );
}

export default function CreateQuestRoute() {
  const params = useLocalSearchParams<{ campaignId?: string | string[] }>();
  const campaignId = typeof params.campaignId === "string" && UUID.test(params.campaignId) ? params.campaignId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [timezoneName, setTimezoneName] = useState<string | null>(null);
  const [options, setOptions] = useState<QuestAuthoringOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sequence = useRef(0);

  const load = useCallback(async () => {
    if (!campaignId || !ownerId) return;
    const request = ++sequence.current;
    setError(null);
    try {
      const [result, preferences, authoringOptions] = await Promise.all([
        campaignApi.get(campaignId),
        preferenceApi.getAvailable(),
        questApi.getAuthoringOptions(),
      ]);
      if (request !== sequence.current) return;
      if (result.status === "archived") {
        setError("Archived campaigns cannot accept new quests.");
        return;
      }
      setCampaign(result);
      setTimezoneName(preferences?.timezoneName ?? null);
      setOptions(authoringOptions);
    } catch (caught) {
      if (request !== sequence.current) return;
      setError(
        caught instanceof CampaignRequestError || caught instanceof QuestRequestError
          ? caught.message
          : "The campaign could not be loaded.",
      );
    }
  }, [campaignId, ownerId]);

  useFocusEffect(useCallback(() => {
    void load();
    return () => { sequence.current += 1; };
  }, [load]));

  if (!ownerId) return null;
  return (
    <KeyboardAwareScreen contentContainerStyle={styles.content}>
      <Stack.Screen options={{ headerBackButtonMenuEnabled: false, title: "Create quest" }} />
      {(!campaign || !options) && !error && campaignId ? <LoadingSkeleton label="Loading quest form" layout="card" /> : null}
      {((!campaign || !options) && error) || !campaignId ? (
        <View style={styles.error}>
          <ErrorState kind="fullScreen" onRetry={campaignId ? () => void load() : undefined} />
          <AppText accessibilityLiveRegion="assertive" tone="error">{campaignId ? error : "This campaign link is invalid."}</AppText>
        </View>
      ) : null}
      {campaign && options ? <QuestForm key={`${ownerId}:${campaign.id}:${campaign.recordVersion}`} campaign={campaign} options={options} ownerId={ownerId} timezoneName={timezoneName} /> : null}
    </KeyboardAwareScreen>
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.xxl },
  fields: { gap: spacing.md, marginVertical: spacing.sm },
  error: { gap: spacing.xs },
});

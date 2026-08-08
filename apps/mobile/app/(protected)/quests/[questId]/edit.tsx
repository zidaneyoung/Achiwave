import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";

import { useAuthentication } from "../../../../src/auth/AuthContext";
import { invalidateCachedCampaign } from "../../../../src/campaigns/cache";
import { AppButton } from "../../../../src/components/AppButton";
import { ErrorState } from "../../../../src/components/ErrorState";
import { AppTextField } from "../../../../src/components/FormControls";
import { LoadingSkeleton } from "../../../../src/components/LoadingSkeleton";
import { PROTECTED_ROUTES } from "../../../../src/navigation/routes";
import { KeyboardAwareScreen } from "../../../../src/platform/KeyboardAwareScreen";
import { questApi, QuestRequestError } from "../../../../src/quests/api";
import { validateOneTimeQuestForm } from "../../../../src/quests/form";
import { QuestOptionSelector } from "../../../../src/quests/QuestOptionSelector";
import type {
  Quest,
  QuestAuthoringOptions,
  QuestCategory,
  QuestDifficulty,
} from "../../../../src/quests/types";
import { AppText } from "../../../../src/theme/AppText";
import { spacing } from "../../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

function QuestEditForm({ quest, options, ownerId, onSaved }: { quest: Quest; options: QuestAuthoringOptions; ownerId: string; onSaved: (quest: Quest) => void }) {
  const [title, setTitle] = useState(quest.title);
  const [description, setDescription] = useState(quest.description ?? "");
  const [category, setCategory] = useState<QuestCategory | null>(quest.category);
  const [difficulty, setDifficulty] = useState<QuestDifficulty | null>(quest.difficulty);
  const [reward, setReward] = useState(String(quest.rewardXp));
  const [attempted, setAttempted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [staleCurrent, setStaleCurrent] = useState<Quest | null>(null);
  const identity = useRef<{ payload: string; mutationId: string } | null>(null);
  const validation = validateOneTimeQuestForm(title, reward, description);

  async function submit() {
    setAttempted(true);
    setSubmissionError(null);
    if (validation.titleError || validation.rewardError || validation.descriptionError || difficulty === null || submitting || staleCurrent) return;
    const payload = JSON.stringify({ title: validation.title, description: validation.description, category, difficulty, rewardXp: validation.rewardXp, version: quest.recordVersion });
    if (identity.current?.payload !== payload) identity.current = { payload, mutationId: questApi.createMutationId() };
    setSubmitting(true);
    try {
      const updated = await questApi.update(quest.id, {
        title: validation.title,
        description: validation.description,
        category,
        difficulty,
        rewardXp: validation.rewardXp,
        recordVersion: quest.recordVersion,
        clientMutationId: identity.current.mutationId,
      });
      invalidateCachedCampaign(ownerId, quest.campaignId);
      AccessibilityInfo.announceForAccessibility("Quest updated.");
      onSaved(updated);
    } catch (caught) {
      const message = caught instanceof QuestRequestError ? caught.message : "The quest could not be updated.";
      if (caught instanceof QuestRequestError && caught.currentQuest) setStaleCurrent(caught.currentQuest);
      setSubmissionError(message);
      AccessibilityInfo.announceForAccessibility(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <AppText accessibilityRole="header" variant="heading1">Edit quest</AppText>
      <AppText tone="muted">Generated occurrence snapshots never change. This occurrence remains {quest.occurrence?.rewardXp ?? 0} XP.</AppText>
      <View style={styles.fields}>
        <AppTextField editable={!submitting && !staleCurrent} errorText={attempted ? validation.titleError ?? undefined : undefined} label="Title" maxLength={121} onChangeText={setTitle} required value={title} />
        <AppTextField
          editable={!submitting && !staleCurrent}
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
          disabled={submitting || staleCurrent !== null}
          helperText="Optional planning label. Uncategorized quests remain valid."
          label="Category"
          nullableLabel="Uncategorized"
          onChange={(value) => setCategory(value as QuestCategory | null)}
          options={options.categories}
          value={category}
        />
        <QuestOptionSelector
          disabled={submitting || staleCurrent !== null}
          errorText={attempted && difficulty === null ? "Choose a difficulty before saving." : undefined}
          helperText="Planning effort only. Difficulty does not determine XP."
          label="Difficulty"
          onChange={(value) => setDifficulty(value as QuestDifficulty | null)}
          options={options.difficulties}
          required
          value={difficulty}
        />
        <AppTextField editable={!submitting && !staleCurrent} errorText={attempted ? validation.rewardError ?? undefined : undefined} keyboardType="number-pad" label="Configured XP reward" onChangeText={setReward} required value={reward} />
      </View>
      {submissionError ? (
        <View style={styles.error}>
          <ErrorState kind="inline" />
          <AppText accessibilityLiveRegion="assertive" tone="error">{submissionError}</AppText>
          {staleCurrent ? <AppText tone="muted">Server version is now {staleCurrent.recordVersion}. Your draft was preserved.</AppText> : null}
        </View>
      ) : null}
      <AppButton disabled={staleCurrent !== null} label="Save quest" loading={submitting} onPress={() => void submit()} />
    </>
  );
}

export default function EditQuestRoute() {
  const params = useLocalSearchParams<{ questId?: string | string[] }>();
  const questId = typeof params.questId === "string" && UUID.test(params.questId) ? params.questId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const router = useRouter();
  const [quest, setQuest] = useState<Quest | null>(null);
  const [options, setOptions] = useState<QuestAuthoringOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sequence = useRef(0);
  const load = useCallback(async () => {
    if (!ownerId || !questId) return;
    const request = ++sequence.current;
    setError(null);
    try {
      const [result, authoringOptions] = await Promise.all([
        questApi.get(questId),
        questApi.getAuthoringOptions(),
      ]);
      if (request !== sequence.current) return;
      if (result.definitionState !== "active" || result.campaignStatus === "archived") {
        setError("Archived quests or campaigns must be restored before editing.");
        return;
      }
      setQuest(result);
      setOptions(authoringOptions);
    } catch (caught) {
      if (request !== sequence.current) return;
      setError(caught instanceof QuestRequestError ? caught.message : "This quest could not be loaded.");
    }
  }, [ownerId, questId]);

  useFocusEffect(useCallback(() => {
    void load();
    return () => { sequence.current += 1; };
  }, [load]));
  if (!ownerId) return null;
  return (
    <KeyboardAwareScreen contentContainerStyle={styles.content}>
      <Stack.Screen options={{ title: "Edit quest" }} />
      {(!quest || !options) && !error && questId ? <LoadingSkeleton label="Loading quest form" layout="card" /> : null}
      {((!quest || !options) && error) || !questId ? (
        <View style={styles.error}>
          <ErrorState kind="fullScreen" onRetry={questId ? () => void load() : undefined} />
          <AppText accessibilityLiveRegion="assertive" tone="error">{questId ? error : "This quest link is invalid."}</AppText>
        </View>
      ) : null}
      {quest && options ? <QuestEditForm key={`${quest.id}:${quest.recordVersion}`} quest={quest} options={options} ownerId={ownerId} onSaved={(saved) => router.replace(PROTECTED_ROUTES.questDetail(saved.id))} /> : null}
    </KeyboardAwareScreen>
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.xxl },
  fields: { gap: spacing.md, marginVertical: spacing.sm },
  error: { gap: spacing.xs },
});

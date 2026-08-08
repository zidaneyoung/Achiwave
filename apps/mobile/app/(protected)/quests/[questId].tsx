import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, ScrollView, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { invalidateCachedCampaign } from "../../../src/campaigns/cache";
import { AppButton } from "../../../src/components/AppButton";
import { ErrorState } from "../../../src/components/ErrorState";
import { LoadingSkeleton } from "../../../src/components/LoadingSkeleton";
import { StatusBadge, type StatusTone } from "../../../src/components/StatusBadge";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { questApi, QuestRequestError } from "../../../src/quests/api";
import type { Quest } from "../../../src/quests/types";
import { AppText } from "../../../src/theme/AppText";
import { type AchiwaveTheme, useThemeStyles } from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

function statusPresentation(quest: Quest): { label: string; tone: StatusTone } {
  const status = quest.definitionState === "archived" ? "archived" : quest.occurrence?.status ?? "active";
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  if (status === "completed") return { label, tone: "success" };
  if (status === "expired" || status === "voided") return { label, tone: "error" };
  if (status === "scheduled") return { label, tone: "warning" };
  if (status === "available" || status === "active") return { label, tone: "info" };
  return { label, tone: "neutral" };
}

export default function QuestDetailRoute() {
  const params = useLocalSearchParams<{ questId?: string | string[] }>();
  const questId = typeof params.questId === "string" && UUID.test(params.questId) ? params.questId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const router = useRouter();
  const styles = useThemeStyles(createStyles);
  const [quest, setQuest] = useState<Quest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [transitioning, setTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const archiveMutationId = useRef<string | null>(null);
  const restoreMutationId = useRef<string | null>(null);
  const sequence = useRef(0);

  const load = useCallback(async () => {
    if (!ownerId || !questId) return;
    const request = ++sequence.current;
    setError(null);
    try {
      const result = await questApi.get(questId);
      if (request === sequence.current) setQuest(result);
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
  if (!questId) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState kind="fullScreen" />
        <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>This quest link is invalid.</AppText>
      </SafeAreaView>
    );
  }
  const presentation = quest ? statusPresentation(quest) : null;
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: quest?.title ?? "Quest" }} />
      {!quest && !error ? <View style={styles.content}><LoadingSkeleton label="Loading quest" layout="card" /></View> : null}
      {!quest && error ? (
        <View style={styles.state}>
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load()} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {quest && presentation ? (
        <ScrollView contentContainerStyle={styles.content}>
          <StatusBadge label={presentation.label} tone={presentation.tone} />
          <AppText accessibilityRole="header" variant="heading1">{quest.title}</AppText>
          {quest.description ? <AppText tone="muted">{quest.description}</AppText> : null}
          <AppText>{quest.rewardXp} XP configured</AppText>
          {quest.occurrence ? (
            <View style={styles.snapshot}>
              <AppText accessibilityRole="header" variant="heading2">Occurrence snapshot</AppText>
              <AppText tone="muted">
                {quest.occurrence.rewardXp} XP · {quest.occurrence.timezoneName} · {quest.occurrence.occurrenceLocalDate}
              </AppText>
            </View>
          ) : null}
          <AppText tone="subtle" variant="caption">
            Record version {quest.recordVersion} · Updated {new Date(quest.updatedAt).toLocaleString()}
          </AppText>
          {quest.definitionState === "active" && quest.campaignStatus !== "archived" ? (
            <AppButton
              icon="pencil-outline"
              label="Edit quest"
              onPress={() => router.push(PROTECTED_ROUTES.questEdit(quest.id))}
            />
          ) : null}
          {quest.campaignStatus !== "archived" ? (
            <AppButton
              label={quest.definitionState === "archived" ? "Restore quest" : "Archive quest"}
              loading={transitioning}
              onPress={() => {
                if (transitioning) return;
                const restoring = quest.definitionState === "archived";
                const mutation = restoring ? restoreMutationId : archiveMutationId;
                mutation.current ??= questApi.createMutationId();
                setTransitioning(true);
                setTransitionError(null);
                const request = restoring
                  ? questApi.restore(quest.id, quest.recordVersion, mutation.current)
                  : questApi.archive(quest.id, quest.recordVersion, mutation.current);
                void request
                  .then(() => {
                    invalidateCachedCampaign(ownerId, quest.campaignId);
                    const message = restoring ? "Quest restored." : "Quest archived.";
                    AccessibilityInfo.announceForAccessibility(message);
                    router.replace(PROTECTED_ROUTES.campaignDetail(quest.campaignId));
                  })
                  .catch((caught) => {
                    const message = caught instanceof QuestRequestError ? caught.message : "The quest lifecycle change failed.";
                    setTransitionError(message);
                    AccessibilityInfo.announceForAccessibility(message);
                  })
                  .finally(() => setTransitioning(false));
              }}
              variant={quest.definitionState === "archived" ? "primary" : "destructive"}
            />
          ) : (
            <AppText tone="muted">Restore the campaign before changing this quest.</AppText>
          )}
          {transitionError ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">{transitionError}</AppText>
            </View>
          ) : null}
          <AppButton
            label="View campaign"
            onPress={() => router.push(PROTECTED_ROUTES.campaignDetail(quest.campaignId))}
            variant="secondary"
          />
        </ScrollView>
      ) : null}
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  content: { gap: spacing.md, padding: spacing.lg },
  state: { flex: 1, gap: spacing.md, justifyContent: "center", padding: spacing.lg },
  snapshot: { gap: spacing.xs },
  center: { textAlign: "center" },
});

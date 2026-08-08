import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, FlatList, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { campaignApi, CampaignRequestError } from "../../../src/campaigns/api";
import {
  getCachedCampaignDetail,
  invalidateCachedCampaign,
  setCachedCampaignDetail,
} from "../../../src/campaigns/cache";
import type {
  CampaignDetail,
  CampaignQuest,
  QuestDisplayStatus,
} from "../../../src/campaigns/types";
import { AppButton } from "../../../src/components/AppButton";
import { AppListItem } from "../../../src/components/ContentSurfaces";
import { EmptyState } from "../../../src/components/EmptyState";
import { ErrorState } from "../../../src/components/ErrorState";
import { LoadingSkeleton } from "../../../src/components/LoadingSkeleton";
import { StatusBadge, type StatusTone } from "../../../src/components/StatusBadge";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { preferenceApi } from "../../../src/preferences/api";
import { formatPreferenceDateTime } from "../../../src/preferences/formatDate";
import type { DateFormatPreference } from "../../../src/preferences/types";
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

function statusPresentation(status: QuestDisplayStatus): { label: string; tone: StatusTone } {
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  if (status === "completed") return { label, tone: "success" };
  if (status === "expired" || status === "voided") return { label, tone: "error" };
  if (status === "scheduled") return { label, tone: "warning" };
  if (status === "available" || status === "active") return { label, tone: "info" };
  return { label, tone: "neutral" };
}

function QuestRow({
  quest,
  dateFormat,
  onPress,
}: {
  quest: CampaignQuest;
  dateFormat: DateFormatPreference | null;
  onPress: () => void;
}) {
  const presentation = statusPresentation(quest.status);
  const due =
    quest.dueAt && quest.timezoneName && dateFormat
      ? ` · Due ${formatPreferenceDateTime(new Date(quest.dueAt), dateFormat, quest.timezoneName)}${quest.dueStatus === "overdue" ? " · Overdue (server confirmed)" : ""}`
      : "";
  return (
    <AppListItem
      onPress={onPress}
      leading={<StatusBadge compact label={presentation.label} tone={presentation.tone} />}
      metadata={`${quest.questType === "one_time" ? "One-time" : "Recurring"} · ${quest.categoryLabel} · ${quest.rewardXp} XP configured${due}`}
      status={quest.description ?? undefined}
      title={quest.title}
    />
  );
}

export default function CampaignDetailRoute() {
  const router = useRouter();
  const parameters = useLocalSearchParams<{ campaignId?: string | string[] }>();
  const rawCampaignId = parameters.campaignId;
  const campaignId = typeof rawCampaignId === "string" && UUID.test(rawCampaignId) ? rawCampaignId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const styles = useThemeStyles(createStyles);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [detail, setDetail] = useState<CampaignDetail | null>(() =>
    ownerId && campaignId ? getCachedCampaignDetail(ownerId, campaignId, false) : null,
  );
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [archiving, setArchiving] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const [dateFormat, setDateFormat] = useState<DateFormatPreference | null>(null);
  const archiveMutationId = useRef<string | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const restoreMutationId = useRef<string | null>(null);
  const requestSequence = useRef(0);

  const load = useCallback(async () => {
    if (!ownerId || !campaignId) return;
    const request = ++requestSequence.current;
    const cached = getCachedCampaignDetail(ownerId, campaignId, includeArchived);
    setDetail(cached);
    setRefreshing(cached !== null);
    setError(null);
    try {
      const [result, preferences] = await Promise.all([
        campaignApi.get(campaignId, includeArchived),
        preferenceApi.getAvailable(),
      ]);
      if (request !== requestSequence.current) return;
      setCachedCampaignDetail(ownerId, campaignId, includeArchived, result);
      setDetail(result);
      setDateFormat(preferences?.dateFormat ?? null);
    } catch (caught) {
      if (request !== requestSequence.current) return;
      setError(
        caught instanceof CampaignRequestError
          ? caught.message
          : "This campaign could not be loaded.",
      );
    } finally {
      if (request === requestSequence.current) setRefreshing(false);
    }
  }, [campaignId, includeArchived, ownerId]);

  useFocusEffect(
    useCallback(() => {
      void load();
      return () => {
        requestSequence.current += 1;
      };
    }, [load]),
  );

  if (!ownerId) return null;
  if (!campaignId) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState kind="fullScreen" />
        <AppText tone="error" style={styles.center}>This campaign link is invalid.</AppText>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: detail?.title ?? "Campaign" }} />
      {!detail && !error ? (
        <View style={styles.state}>
          <LoadingSkeleton label="Loading campaign details" layout="card" />
          <LoadingSkeleton label="Loading campaign quests" layout="list" />
        </View>
      ) : null}
      {!detail && error ? (
        <View style={styles.state}>
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load()} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {detail ? (
        <FlatList
          contentContainerStyle={styles.content}
          data={detail.quests}
          keyExtractor={(quest) => quest.id}
          ListHeaderComponent={
            <View style={styles.header}>
              <StatusBadge
                label={detail.status.charAt(0).toUpperCase() + detail.status.slice(1)}
                tone={detail.status === "completed" ? "success" : detail.status === "archived" ? "neutral" : "info"}
              />
              <AppText accessibilityRole="header" variant="heading1">{detail.title}</AppText>
              {detail.description ? <AppText tone="muted">{detail.description}</AppText> : null}
              <AppText tone="subtle" variant="caption">
                Record version {detail.recordVersion} · Created {new Date(detail.createdAt).toLocaleString()} · Updated {new Date(detail.updatedAt).toLocaleString()}
              </AppText>
              <AppText variant="label">
                {detail.questSummary.active} active · {detail.questSummary.archived} archived quests
              </AppText>
              <AppButton
                icon="pencil-outline"
                label="Edit campaign"
                onPress={() => router.push(PROTECTED_ROUTES.campaignEdit(detail.id))}
                variant="secondary"
              />
              <AppButton
                label={includeArchived ? "Hide archived quests" : "Show archived quests"}
                onPress={() => {
                  setIncludeArchived((current) => !current);
                  setDetail(null);
                  setError(null);
                }}
                variant="secondary"
              />
              {detail.status !== "archived" ? (
                <AppButton
                  label="Archive campaign"
                  loading={archiving}
                  onPress={() => {
                    if (archiving) return;
                    archiveMutationId.current ??= campaignApi.createMutationId();
                    setArchiving(true);
                    setArchiveError(null);
                    void campaignApi
                      .archive(detail.id, detail.recordVersion, archiveMutationId.current)
                      .then(() => {
                        AccessibilityInfo.announceForAccessibility("Campaign archived.");
                        invalidateCachedCampaign(ownerId, detail.id);
                        router.replace(PROTECTED_ROUTES.campaigns);
                      })
                      .catch((caught) => {
                        const message =
                          caught instanceof CampaignRequestError
                            ? caught.message
                            : "The campaign could not be archived.";
                        setArchiveError(message);
                        AccessibilityInfo.announceForAccessibility(message);
                      })
                      .finally(() => setArchiving(false));
                  }}
                  variant="destructive"
                />
              ) : (
                <AppButton
                  label="Restore campaign"
                  loading={restoring}
                  onPress={() => {
                    if (restoring) return;
                    restoreMutationId.current ??= campaignApi.createMutationId();
                    setRestoring(true);
                    setRestoreError(null);
                    void campaignApi
                      .restore(detail.id, detail.recordVersion, restoreMutationId.current)
                      .then(() => {
                        AccessibilityInfo.announceForAccessibility("Campaign restored.");
                        invalidateCachedCampaign(ownerId, detail.id);
                        router.replace(PROTECTED_ROUTES.campaigns);
                      })
                      .catch((caught) => {
                        const message =
                          caught instanceof CampaignRequestError
                            ? caught.message
                            : "The campaign could not be restored.";
                        setRestoreError(message);
                        AccessibilityInfo.announceForAccessibility(message);
                      })
                      .finally(() => setRestoring(false));
                  }}
                  variant="primary"
                />
              )}
              {archiveError ? (
                <View style={styles.footer}>
                  <ErrorState kind="inline" />
                  <AppText accessibilityLiveRegion="assertive" tone="error">{archiveError}</AppText>
                </View>
              ) : null}
              {restoreError ? (
                <View style={styles.footer}>
                  <ErrorState kind="inline" />
                  <AppText accessibilityLiveRegion="assertive" tone="error">{restoreError}</AppText>
                </View>
              ) : null}
              <AppText accessibilityRole="header" variant="heading2">Quests</AppText>
              {detail.status === "active" ? (
                <AppButton
                  icon="plus"
                  label="Create one-time quest"
                  onPress={() => router.push(PROTECTED_ROUTES.questCreate(detail.id))}
                />
              ) : null}
            </View>
          }
          ListEmptyComponent={
            <EmptyState
              description={includeArchived ? "This campaign has no quest definitions." : "Add a quest when you are ready to plan the objective."}
              kind="firstUse"
              title={includeArchived ? "No quests in history" : "No active quests"}
            />
          }
          ListFooterComponent={
            error ? (
              <View style={styles.footer}>
                <ErrorState kind="section" onRetry={() => void load()} />
                <AppText accessibilityLiveRegion="assertive" tone="error">{error}</AppText>
              </View>
            ) : refreshing ? (
              <AppText accessibilityLiveRegion="polite" tone="muted" style={styles.center}>Refreshing campaign…</AppText>
            ) : null
          }
          renderItem={({ item }) => (
            <QuestRow
              dateFormat={dateFormat}
              quest={item}
              onPress={() => router.push(PROTECTED_ROUTES.questDetail(item.id))}
            />
          )}
        />
      ) : null}
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  state: { flex: 1, gap: spacing.md, justifyContent: "center", padding: spacing.lg },
  content: { gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.xxl },
  header: { gap: spacing.sm, marginBottom: spacing.sm },
  footer: { gap: spacing.xs, marginTop: spacing.md },
  center: { textAlign: "center" },
});

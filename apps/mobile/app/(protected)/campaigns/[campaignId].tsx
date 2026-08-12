import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { useReducedMotion } from "../../../src/accessibility/ReducedMotionProvider";
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
import { AppDialog } from "../../../src/components/Overlays";
import { StatusBadge, type StatusTone } from "../../../src/components/StatusBadge";
import { campaignArchiveConfirmation } from "../../../src/lifecycle/archiveConfirmation";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { preferenceApi } from "../../../src/preferences/api";
import { formatPreferenceDateTime } from "../../../src/preferences/formatDate";
import type { DateFormatPreference } from "../../../src/preferences/types";
import { questApi, QuestRequestError } from "../../../src/quests/api";
import { applyQuestOrder, moveQuest, type QuestMoveDirection } from "../../../src/quests/reorder";
import { createKeyedSingleFlight } from "../../../src/refresh/singleFlight";
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
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
  busy,
  index,
  reorderEnabled,
  total,
  onMove,
  onPress,
}: {
  quest: CampaignQuest;
  dateFormat: DateFormatPreference | null;
  busy: boolean;
  index: number;
  reorderEnabled: boolean;
  total: number;
  onMove: (direction: QuestMoveDirection) => void;
  onPress: () => void;
}) {
  const presentation = statusPresentation(quest.status);
  const due =
    quest.dueAt && quest.timezoneName
      ? ` · Due ${formatPreferenceDateTime(new Date(quest.dueAt), dateFormat ?? "system", quest.timezoneName)}${quest.dueStatus === "overdue" ? " · Overdue (server confirmed)" : ""}`
      : "";
  return (
    <View style={questRowStyles.questBlock}>
      <AppListItem
        onPress={onPress}
        leading={<StatusBadge compact label={presentation.label} tone={presentation.tone} />}
        metadata={`${quest.questType === "one_time" ? "One-time" : "Recurring"} · ${quest.categoryLabel} · Difficulty ${quest.difficultyLabel} · ${quest.rewardXp} XP configured${due}`}
        status={quest.description ?? undefined}
        title={quest.title}
      />
      {quest.definitionState === "active" ? (
        <View style={questRowStyles.orderActions}>
          <AppButton
            accessibilityHint={`Moves ${quest.title} one position earlier.`}
            disabled={!reorderEnabled || busy || index === 0}
            icon="arrow-up"
            label={`Move ${quest.title} up`}
            onPress={() => onMove("up")}
            variant="secondary"
          />
          <AppButton
            accessibilityHint={`Moves ${quest.title} one position later.`}
            disabled={!reorderEnabled || busy || index === total - 1}
            icon="arrow-down"
            label={`Move ${quest.title} down`}
            onPress={() => onMove("down")}
            variant="secondary"
          />
        </View>
      ) : null}
    </View>
  );
}

export default function CampaignDetailRoute() {
  const router = useRouter();
  const parameters = useLocalSearchParams<{ campaignId?: string | string[] }>();
  const rawCampaignId = parameters.campaignId;
  const campaignId = typeof rawCampaignId === "string" && UUID.test(rawCampaignId) ? rawCampaignId : null;
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated" ? authentication.state.user.id : null;
  const reduceMotion = useReducedMotion();
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [detail, setDetail] = useState<CampaignDetail | null>(() =>
    ownerId && campaignId ? getCachedCampaignDetail(ownerId, campaignId, false) : null,
  );
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [archiving, setArchiving] = useState(false);
  const [archiveDialogVisible, setArchiveDialogVisible] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const [dateFormat, setDateFormat] = useState<DateFormatPreference | null>(null);
  const archivePending = useRef(false);
  const archiveRequest = useRef<{ mutationId: string; recordVersion: number } | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const restoreMutationId = useRef<string | null>(null);
  const [reordering, setReordering] = useState(false);
  const [reorderError, setReorderError] = useState<string | null>(null);
  const reorderIdentity = useRef<{ payload: string; mutationId: string } | null>(null);
  const requestSequence = useRef(0);
  const contentRef = useRef(detail);
  const manualRefreshRef = useRef(false);
  const manualRefreshGeneration = useRef(0);
  const [requests] = useState(() => createKeyedSingleFlight<{
    detail: CampaignDetail;
    dateFormat: DateFormatPreference | null;
  }>());
  contentRef.current = detail;

  const load = useCallback(async (reason: "focus" | "manual" | "retry" = "focus") => {
    if (!ownerId || !campaignId) return;
    let manualGeneration: number | null = null;
    if (reason === "manual") {
      if (manualRefreshRef.current) return;
      manualRefreshRef.current = true;
      manualGeneration = ++manualRefreshGeneration.current;
      setRefreshing(true);
    }
    const request = ++requestSequence.current;
    const cached = getCachedCampaignDetail(ownerId, campaignId, includeArchived);
    if (contentRef.current === null && cached !== null) {
      contentRef.current = cached;
      setDetail(cached);
    }
    const hadContent = contentRef.current !== null;
    if (hadContent) setRefreshError(null);
    else setError(null);
    try {
      const { promise } = requests.run(
        `${ownerId}:${campaignId}:${includeArchived ? "history" : "active"}`,
        async () => {
          const [result, preferences] = await Promise.all([
            campaignApi.get(campaignId, includeArchived),
            preferenceApi.getAvailable(),
          ]);
          return {
            detail: result,
            dateFormat: preferences?.dateFormat ?? null,
          };
        },
      );
      const result = await promise;
      if (request !== requestSequence.current) return;
      setCachedCampaignDetail(ownerId, campaignId, includeArchived, result.detail);
      contentRef.current = result.detail;
      setDetail(result.detail);
      setDateFormat(result.dateFormat);
      setError(null);
      setRefreshError(null);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility("Campaign refreshed.");
      }
    } catch (caught) {
      if (request !== requestSequence.current) return;
      const message = caught instanceof CampaignRequestError
        ? caught.message
        : "This campaign could not be loaded.";
      if (hadContent) setRefreshError(message);
      else setError(message);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility(`Campaign refresh failed. ${message}`);
      }
    } finally {
      if (reason === "manual" && manualGeneration === manualRefreshGeneration.current) {
        manualRefreshRef.current = false;
        setRefreshing(false);
      }
    }
  }, [campaignId, includeArchived, ownerId, requests]);

  async function reorderQuest(index: number, direction: QuestMoveDirection) {
    if (!detail || !ownerId || includeArchived || reordering) return;
    const activeQuests = detail.quests.filter((quest) => quest.definitionState === "active");
    const reordered = moveQuest(activeQuests, index, direction);
    if (!reordered) return;
    const payload = JSON.stringify({
      campaignRecordVersion: detail.recordVersion,
      items: reordered.map((quest) => ({ id: quest.id, recordVersion: quest.recordVersion })),
    });
    if (reorderIdentity.current?.payload !== payload) {
      reorderIdentity.current = { payload, mutationId: questApi.createMutationId() };
    }
    const movedQuest = activeQuests[index];
    setReordering(true);
    setReorderError(null);
    try {
      const result = await questApi.reorderActive(detail.id, {
        campaignRecordVersion: detail.recordVersion,
        items: reordered.map((quest) => ({
          id: quest.id,
          recordVersion: quest.recordVersion,
        })),
        clientMutationId: reorderIdentity.current.mutationId,
      });
      const canonical = applyQuestOrder(detail, result);
      setDetail(canonical);
      setCachedCampaignDetail(ownerId, detail.id, false, canonical);
      AccessibilityInfo.announceForAccessibility(
        `${movedQuest.title} moved ${direction}.`,
      );
    } catch (caught) {
      if (caught instanceof QuestRequestError && caught.currentOrder) {
        const canonical = applyQuestOrder(detail, caught.currentOrder);
        setDetail(canonical);
        setCachedCampaignDetail(ownerId, detail.id, false, canonical);
      }
      const message = caught instanceof QuestRequestError
        ? caught.message
        : "The quest order could not be changed.";
      setReorderError(message);
      AccessibilityInfo.announceForAccessibility(message);
    } finally {
      setReordering(false);
    }
  }

  function archiveCampaign() {
    if (!detail || !ownerId || archivePending.current) return;
    archivePending.current = true;
    archiveRequest.current ??= {
      mutationId: campaignApi.createMutationId(),
      recordVersion: detail.recordVersion,
    };
    setArchiving(true);
    setArchiveError(null);
    void campaignApi
      .archive(
        detail.id,
        archiveRequest.current.recordVersion,
        archiveRequest.current.mutationId,
      )
      .then(() => {
        setArchiveDialogVisible(false);
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
      .finally(() => {
        archivePending.current = false;
        setArchiving(false);
      });
  }

  useFocusEffect(
    useCallback(() => {
      void load("focus");
      return () => {
        requestSequence.current += 1;
        manualRefreshGeneration.current += 1;
        manualRefreshRef.current = false;
        setRefreshing(false);
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
  const archiveConfirmation = detail ? campaignArchiveConfirmation(detail.title) : null;

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
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load("retry")} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {detail ? (
        <FlatList
          contentContainerStyle={styles.content}
          data={detail.quests}
          keyExtractor={(quest) => quest.id}
          refreshControl={
            <RefreshControl
              colors={[theme.colors.accent]}
              enabled={!refreshing && !reordering && !archiving && !restoring}
              onRefresh={() => void load("manual")}
              progressBackgroundColor={theme.colors.surface}
              refreshing={refreshing && !reduceMotion}
              tintColor={theme.colors.accent}
            />
          }
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
                  requestSequence.current += 1;
                  manualRefreshGeneration.current += 1;
                  manualRefreshRef.current = false;
                  setRefreshing(false);
                  setIncludeArchived((current) => !current);
                  contentRef.current = null;
                  setDetail(null);
                  setError(null);
                  setRefreshError(null);
                  setReorderError(null);
                }}
                variant="secondary"
              />
              {detail.status !== "archived" ? (
                <AppButton
                  label="Archive campaign"
                  onPress={() => {
                    archiveRequest.current = null;
                    setArchiveError(null);
                    setArchiveDialogVisible(true);
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
              {restoreError ? (
                <View style={styles.footer}>
                  <ErrorState kind="inline" />
                  <AppText accessibilityLiveRegion="assertive" tone="error">{restoreError}</AppText>
                </View>
              ) : null}
              <AppText accessibilityRole="header" variant="heading2">Quests</AppText>
              {includeArchived ? (
                <AppText tone="muted">
                  Reordering is disabled while archived quests are shown. Hide archived quests to change active order.
                </AppText>
              ) : null}
              {detail.status !== "archived" ? (
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
            reorderError ? (
              <View style={styles.footer}>
                <ErrorState kind="inline" />
                <AppText accessibilityLiveRegion="assertive" tone="error">{reorderError}</AppText>
              </View>
            ) : refreshError ? (
              <View style={styles.footer}>
                <ErrorState kind="section" onRetry={() => void load("retry")} />
                <AppText accessibilityLiveRegion="assertive" tone="error">
                  Campaign refresh failed. {refreshError}
                </AppText>
              </View>
            ) : refreshing && reduceMotion ? (
              <AppText accessibilityLiveRegion="polite" tone="muted" style={styles.center}>Refreshing campaign…</AppText>
            ) : null
          }
          renderItem={({ item, index }) => (
            <QuestRow
              busy={reordering}
              dateFormat={dateFormat}
              index={index}
              quest={item}
              reorderEnabled={!includeArchived && detail.status !== "archived" && detail.quests.length > 1}
              total={detail.quests.length}
              onMove={(direction) => void reorderQuest(index, direction)}
              onPress={() => router.push(PROTECTED_ROUTES.questDetail(item.id))}
            />
          )}
        />
      ) : null}
      {detail && archiveConfirmation && detail.status !== "archived" ? (
        <AppDialog
          busy={archiving}
          confirmLabel="Archive"
          description={archiveConfirmation.description}
          dismissLabel="Cancel"
          kind="destructive"
          onConfirm={archiveCampaign}
          onDismiss={() => {
            if (archivePending.current) return;
            setArchiveDialogVisible(false);
            setArchiveError(null);
          }}
          title={archiveConfirmation.title}
          visible={archiveDialogVisible}
        >
          {archiveError ? (
            <View style={styles.dialogError}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">{archiveError}</AppText>
            </View>
          ) : null}
        </AppDialog>
      ) : null}
    </SafeAreaView>
  );
}

const questRowStyles = StyleSheet.create({
  questBlock: { gap: spacing.xs },
  orderActions: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
});

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  state: { flex: 1, gap: spacing.md, justifyContent: "center", padding: spacing.lg },
  content: { gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.xxl },
  header: { gap: spacing.sm, marginBottom: spacing.sm },
  footer: { gap: spacing.xs, marginTop: spacing.md },
  dialogError: { gap: spacing.xs },
  center: { textAlign: "center" },
});

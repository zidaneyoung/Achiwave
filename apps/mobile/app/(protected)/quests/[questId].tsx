import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { AccessibilityInfo, RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { useReducedMotion } from "../../../src/accessibility/ReducedMotionProvider";
import { invalidateCachedCampaign } from "../../../src/campaigns/cache";
import { AppButton } from "../../../src/components/AppButton";
import {
  completionApi,
  CompletionRequestError,
  type CompleteOccurrenceInput,
} from "../../../src/completions/api";
import type { CompleteOccurrenceResult } from "../../../src/completions/types";
import { CompletionSubmissionRegistry } from "../../../src/completions/submission";
import { classifyCompletionFailure } from "../../../src/completions/failure";
import { completionQueue } from "../../../src/completions/queue";
import {
  manuallyRetryCompletion,
  subscribeCompletionRefresh,
  synchronizeCompletionQueue,
} from "../../../src/completions/sync";
import { useCompletionQueueRecord } from "../../../src/completions/useCompletionQueueRecord";
import {
  completionQueueStatePresentation,
  isCompletionQueueRecordRelevant,
} from "../../../src/completions/queuePresentation";
import {
  beginCompletionPresentation,
  clearCompletionPresentation,
  confirmCompletionPresentation,
  failCompletionPresentation,
  getCompletionPresentation,
  refreshCompletionCanonical,
  subscribeCompletionPresentation,
} from "../../../src/completions/presentation";
import { ErrorState } from "../../../src/components/ErrorState";
import { LoadingSkeleton } from "../../../src/components/LoadingSkeleton";
import { AppDialog } from "../../../src/components/Overlays";
import { StatusBadge, type StatusTone } from "../../../src/components/StatusBadge";
import { questArchiveConfirmation } from "../../../src/lifecycle/archiveConfirmation";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { questApi, QuestRequestError } from "../../../src/quests/api";
import type { Quest } from "../../../src/quests/types";
import { createKeyedSingleFlight } from "../../../src/refresh/singleFlight";
import { preferenceApi } from "../../../src/preferences/api";
import { formatPreferenceDateTime } from "../../../src/preferences/formatDate";
import type { DateFormatPreference } from "../../../src/preferences/types";
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;
const completionSubmissions = new CompletionSubmissionRegistry<
  CompleteOccurrenceInput,
  CompleteOccurrenceResult
>();

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
  const reduceMotion = useReducedMotion();
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [quest, setQuest] = useState<Quest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
  const [manualRetrying, setManualRetrying] = useState(false);
  const [reversing, setReversing] = useState(false);
  const [reversalDialogVisible, setReversalDialogVisible] = useState(false);
  const [reversalError, setReversalError] = useState<string | null>(null);
  const [archiveDialogVisible, setArchiveDialogVisible] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const [dateFormat, setDateFormat] = useState<DateFormatPreference | null>(null);
  const archivePending = useRef(false);
  const completionPending = useRef(false);
  const reversalPending = useRef(false);
  const reversalRequest = useRef<{
    completionId: string;
    mutationId: string;
    recordVersion: number;
  } | null>(null);
  const archiveRequest = useRef<{ mutationId: string; recordVersion: number } | null>(null);
  const restoreMutationId = useRef<string | null>(null);
  const sequence = useRef(0);
  const announcedQueueStates = useRef(new Map<string, string>());
  const contentRef = useRef(quest);
  const manualRefreshRef = useRef(false);
  const manualRefreshGeneration = useRef(0);
  const [requests] = useState(() => createKeyedSingleFlight<{
    dateFormat: DateFormatPreference | null;
    quest: Quest;
  }>());
  contentRef.current = quest;
  const presentationOccurrenceId = quest?.occurrence?.id ?? null;
  const completionPresentation = useSyncExternalStore(
    useCallback(
      (listener) => subscribeCompletionPresentation(
        ownerId,
        presentationOccurrenceId,
        listener,
      ),
      [ownerId, presentationOccurrenceId],
    ),
    useCallback(
      () => getCompletionPresentation(ownerId, presentationOccurrenceId),
      [ownerId, presentationOccurrenceId],
    ),
  );
  const storedQueuedCompletion = useCompletionQueueRecord(
    ownerId,
    presentationOccurrenceId,
  );
  const queuedCompletion = storedQueuedCompletion &&
    isCompletionQueueRecordRelevant(
      storedQueuedCompletion,
      quest?.occurrence?.activeCompletionId ?? null,
    )
    ? storedQueuedCompletion
    : null;
  useEffect(() => {
    if (!queuedCompletion) return;
    const previous = announcedQueueStates.current.get(queuedCompletion.queueId);
    if (previous && previous !== queuedCompletion.state) {
      AccessibilityInfo.announceForAccessibility(
        completionQueueStatePresentation(queuedCompletion.state).announcement,
      );
    }
    announcedQueueStates.current.set(queuedCompletion.queueId, queuedCompletion.state);
  }, [queuedCompletion]);

  const load = useCallback(async (reason: "focus" | "manual" | "retry" = "focus") => {
    if (!ownerId || !questId) return;
    let manualGeneration: number | null = null;
    if (reason === "manual") {
      if (manualRefreshRef.current) return;
      manualRefreshRef.current = true;
      manualGeneration = ++manualRefreshGeneration.current;
      setRefreshing(true);
    }
    const request = ++sequence.current;
    const hadContent = contentRef.current !== null;
    if (hadContent) setRefreshError(null);
    else setError(null);
    try {
      const { promise } = requests.run(`${ownerId}:${questId}`, async () => {
        const [result, preferences] = await Promise.all([
          questApi.get(questId),
          preferenceApi.getAvailable(),
        ]);
        return {
          dateFormat: preferences?.dateFormat ?? null,
          quest: result,
        };
      });
      const result = await promise;
      if (request !== sequence.current) return;
      contentRef.current = result.quest;
      refreshCompletionCanonical(ownerId, result.quest);
      setQuest(result.quest);
      setDateFormat(result.dateFormat);
      setError(null);
      setRefreshError(null);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility("Quest refreshed.");
      }
    } catch (caught) {
      if (request !== sequence.current) return;
      const message = caught instanceof QuestRequestError
        ? caught.message
        : "This quest could not be loaded.";
      if (hadContent) setRefreshError(message);
      else setError(message);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility(`Quest refresh failed. ${message}`);
      }
    } finally {
      if (reason === "manual" && manualGeneration === manualRefreshGeneration.current) {
        manualRefreshRef.current = false;
        setRefreshing(false);
      }
    }
  }, [ownerId, questId, requests]);

  function archiveQuest() {
    if (!quest || !ownerId || archivePending.current) return;
    archivePending.current = true;
    archiveRequest.current ??= {
      mutationId: questApi.createMutationId(),
      recordVersion: quest.recordVersion,
    };
    setTransitioning(true);
    setArchiveError(null);
    void questApi
      .archive(
        quest.id,
        archiveRequest.current.recordVersion,
        archiveRequest.current.mutationId,
      )
      .then(() => {
        setArchiveDialogVisible(false);
        invalidateCachedCampaign(ownerId, quest.campaignId);
        AccessibilityInfo.announceForAccessibility("Quest archived.");
        router.replace(PROTECTED_ROUTES.campaignDetail(quest.campaignId));
      })
      .catch((caught) => {
        const message = caught instanceof QuestRequestError
          ? caught.message
          : "The quest could not be archived.";
        setArchiveError(message);
        AccessibilityInfo.announceForAccessibility(message);
      })
      .finally(() => {
        archivePending.current = false;
        setTransitioning(false);
      });
  }

  function completeOccurrence() {
    if (!quest?.occurrence || !ownerId || completionPending.current) return;
    const occurrence = quest.occurrence;
    const key = `${ownerId}:${occurrence.id}`;
    if (completionPresentation?.phase === "permanent_failure") return;
    const submission = completionSubmissions.run(
      key,
      () => ({
        clientMutationId: completionApi.createMutationId(),
        deviceObservedAt: new Date().toISOString(),
        deviceTimezoneName: occurrence.timezoneName,
        expectedOccurrenceVersion: occurrence.recordVersion,
        occurrenceId: occurrence.id,
      }),
      (input) => completionApi.complete(input),
    );
    beginCompletionPresentation(ownerId, quest, submission.input);
    completionPending.current = true;
    setCompleting(true);
    void submission.promise.then(async (result) => {
      await completionQueue.recordSynchronized(ownerId, submission.input, result);
      confirmCompletionPresentation(ownerId, result);
      setQuest((current) => current?.occurrence ? {
        ...current,
        campaignRecordVersion: result.campaign.recordVersion,
        campaignStatus: result.campaign.status,
        occurrence: {
          ...current.occurrence,
          activeCompletionId: result.completion.id,
          completedAt: result.occurrence.completedAt,
          recordVersion: result.occurrence.recordVersion,
          reversedAt: result.occurrence.reversedAt,
          status: result.occurrence.status,
        },
      } : current);
      invalidateCachedCampaign(ownerId, result.campaign.id);
      AccessibilityInfo.announceForAccessibility(
        result.outcome === "duplicate_completion"
          ? "Quest was already completed and is synchronized."
          : "Quest completion confirmed by the server.",
      );
    }).catch(async (caught) => {
      const failure = classifyCompletionFailure(caught);
      if (failure.kind === "retryable_failure") {
        try {
          const queued = await completionQueue.enqueue(ownerId, submission.input);
          completionSubmissions.clear(key);
          AccessibilityInfo.announceForAccessibility(
            queued.reused
              ? "Completion is already pending and will synchronize after reconnection."
              : "Completion saved as pending and will synchronize after reconnection.",
          );
          void synchronizeCompletionQueue(ownerId);
          return;
        } catch {
          // Fall through to the safe retryable failure presentation.
        }
      }
      const failed = failCompletionPresentation(
        ownerId,
        occurrence.id,
        submission.input.clientMutationId,
        failure,
      );
      if (failure.kind === "permanent_failure") completionSubmissions.clear(key);
      if (failure.refreshCanonical) void load("retry");
      if (failed.changed) {
        AccessibilityInfo.announceForAccessibility(
          `${failure.message} ${failure.nextAction}.`,
        );
      }
    }).finally(() => {
      completionPending.current = false;
      setCompleting(false);
    });
  }

  function reverseCompletion() {
    if (!quest?.occurrence?.activeCompletionId || !ownerId || reversalPending.current) return;
    reversalRequest.current ??= {
      completionId: quest.occurrence.activeCompletionId,
      mutationId: completionApi.createMutationId(),
      recordVersion: quest.occurrence.recordVersion,
    };
    reversalPending.current = true;
    setReversing(true);
    setReversalError(null);
    void completionApi.reverse({
      clientMutationId: reversalRequest.current.mutationId,
      completionId: reversalRequest.current.completionId,
      expectedOccurrenceVersion: reversalRequest.current.recordVersion,
    }).then((result) => {
      setQuest((current) => current?.occurrence ? {
        ...current,
        campaignRecordVersion: result.campaign.recordVersion,
        campaignStatus: result.campaign.status,
        occurrence: {
          ...current.occurrence,
          activeCompletionId: null,
          completedAt: result.occurrence.completedAt,
          recordVersion: result.occurrence.recordVersion,
          reversedAt: result.occurrence.reversedAt,
          status: result.occurrence.status,
        },
      } : current);
      reversalRequest.current = null;
      setReversalDialogVisible(false);
      invalidateCachedCampaign(ownerId, result.campaign.id);
      AccessibilityInfo.announceForAccessibility(
        result.outcome === "already_reversed"
          ? "Completion was already reversed and is synchronized."
          : "Completion reversal confirmed by the server.",
      );
    }).catch((caught) => {
      const message = caught instanceof CompletionRequestError
        ? caught.message
        : "The completion could not be reversed.";
      setReversalError(message);
      AccessibilityInfo.announceForAccessibility(message);
    }).finally(() => {
      reversalPending.current = false;
      setReversing(false);
    });
  }

  function retryQueuedCompletion(): void {
    if (!ownerId || !queuedCompletion || manualRetrying) return;
    setManualRetrying(true);
    void manuallyRetryCompletion(ownerId, queuedCompletion.queueId)
      .then((result) => {
        if (
          result.outcome === "authentication_required" ||
          result.outcome === "offline" ||
          result.outcome === "not_eligible"
        ) {
          AccessibilityInfo.announceForAccessibility(result.message);
        }
      })
      .finally(() => setManualRetrying(false));
  }

  function dismissQueuedFailure(): void {
    if (!ownerId || !queuedCompletion || queuedCompletion.state !== "permanent_failure") return;
    void completionQueue
      .dismissPermanentFailure(ownerId, queuedCompletion.queueId)
      .then((dismissed) => {
        if (!dismissed) return;
        clearCompletionPresentation(ownerId, queuedCompletion.occurrenceId);
        AccessibilityInfo.announceForAccessibility(
          "Local failure dismissed. Refreshing the latest quest state.",
        );
        void load("manual");
      });
  }

  useFocusEffect(useCallback(() => {
    void load("focus");
    return () => {
      sequence.current += 1;
      manualRefreshGeneration.current += 1;
      manualRefreshRef.current = false;
      setRefreshing(false);
    };
  }, [load]));

  useEffect(
    () => subscribeCompletionRefresh((occurrenceId) => {
      if (occurrenceId === presentationOccurrenceId) void load("retry");
    }),
    [load, presentationOccurrenceId],
  );

  if (!ownerId) return null;
  if (!questId) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ErrorState kind="fullScreen" />
        <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>This quest link is invalid.</AppText>
      </SafeAreaView>
    );
  }
  const archiveConfirmation = quest ? questArchiveConfirmation(quest.title) : null;
  const presentation = quest ? statusPresentation(quest) : null;
  const queuePresentation = queuedCompletion
    ? completionQueueStatePresentation(queuedCompletion.state)
    : null;
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <Stack.Screen options={{ title: quest?.title ?? "Quest" }} />
      {!quest && !error ? <View style={styles.content}><LoadingSkeleton label="Loading quest" layout="card" /></View> : null}
      {!quest && error ? (
        <View style={styles.state}>
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load("retry")} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {quest && presentation ? (
        <ScrollView
          contentContainerStyle={styles.content}
          refreshControl={
            <RefreshControl
              colors={[theme.colors.accent]}
              enabled={!refreshing && !transitioning}
              onRefresh={() => void load("manual")}
              progressBackgroundColor={theme.colors.surface}
              refreshing={refreshing && !reduceMotion}
              tintColor={theme.colors.accent}
            />
          }
        >
          <StatusBadge label={presentation.label} tone={presentation.tone} />
          {queuePresentation ? (
            <StatusBadge label={queuePresentation.label} tone={queuePresentation.tone} />
          ) : completionPresentation?.phase === "pending" ? (
            <StatusBadge label="Pending completion — awaiting server confirmation" tone="warning" />
          ) : null}
          {!queuedCompletion && completionPresentation?.phase === "synchronized" ? (
            <StatusBadge label="Completion synchronized with the server" tone="success" />
          ) : null}
          {!queuedCompletion && completionPresentation?.phase === "retryable_failure" ? (
            <StatusBadge label="Completion not synchronized — retry available" tone="error" />
          ) : null}
          {!queuedCompletion && completionPresentation?.phase === "permanent_failure" ? (
            <StatusBadge label="Completion rejected — canonical state restored" tone="error" />
          ) : null}
          <AppText accessibilityRole="header" variant="heading1">{quest.title}</AppText>
          {quest.description ? <AppText tone="muted">{quest.description}</AppText> : null}
          <AppText>Category: {quest.categoryLabel}</AppText>
          <AppText>Difficulty: {quest.difficultyLabel}</AppText>
          <AppText>{quest.rewardXp} XP configured</AppText>
          {quest.dueAt && quest.timezoneName ? (
            <View style={styles.snapshot}>
              <AppText accessibilityRole="header" variant="heading2">Due</AppText>
              <AppText>
                {formatPreferenceDateTime(new Date(quest.dueAt), dateFormat ?? "system", quest.timezoneName)} ({quest.timezoneName})
              </AppText>
              {quest.dueStatus === "overdue" ? (
                <AppText accessibilityLiveRegion="polite" tone="error">Overdue — confirmed by the server.</AppText>
              ) : null}
              {quest.dueStatus === "unavailable" ? (
                <AppText tone="muted">This due occurrence is no longer available.</AppText>
              ) : null}
            </View>
          ) : null}
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
          {quest.occurrence &&
          quest.definitionState === "active" &&
          quest.campaignStatus === "active" &&
          (quest.occurrence.status === "available" || quest.occurrence.status === "reversed") ? (
            <AppButton
              accessibilityHint="Submits this occurrence to the server for authoritative completion."
              icon="check-circle-outline"
              disabled={queuedCompletion !== null || completionPresentation?.phase === "permanent_failure"}
              label={completionPresentation?.phase === "retryable_failure" ? "Retry completion" : "Complete quest"}
              loading={
                completing ||
                completionPresentation?.phase === "pending" ||
                queuedCompletion?.state === "pending" ||
                queuedCompletion?.state === "in_flight"
              }
              onPress={completeOccurrence}
            />
          ) : null}
          {!queuedCompletion && completionPresentation &&
          (completionPresentation.phase === "retryable_failure" ||
            completionPresentation.phase === "permanent_failure") ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">
                {completionPresentation.failure.message} {completionPresentation.failure.nextAction}.
              </AppText>
              {completionPresentation.phase === "permanent_failure" ? (
                <AppButton
                  label="Review refreshed quest"
                  onPress={() => {
                    clearCompletionPresentation(ownerId, quest.occurrence?.id ?? "");
                    void load("manual");
                  }}
                  variant="secondary"
                />
              ) : null}
            </View>
          ) : null}
          {queuedCompletion?.state === "retryable_failure" ||
          queuedCompletion?.state === "permanent_failure" ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="polite" tone="error">
                {queuedCompletion.safeErrorMessage ?? queuePresentation?.announcement}
              </AppText>
              {queuedCompletion.state === "permanent_failure" ? (
                <AppButton
                  accessibilityHint="Removes local failure evidence and refreshes canonical server state."
                  label="Dismiss and refresh quest"
                  onPress={dismissQueuedFailure}
                  variant="secondary"
                />
              ) : null}
            </View>
          ) : null}
          {queuedCompletion?.state === "cancelled" ? (
            <AppText accessibilityLiveRegion="polite" tone="muted">
              {queuePresentation?.announcement}
            </AppText>
          ) : null}
          {queuedCompletion?.state === "retryable_failure" ||
          (queuedCompletion?.state === "in_flight" && manualRetrying) ? (
            <AppButton
              accessibilityHint="Checks connectivity and authentication, then retries this exact pending completion once."
              accessibilityLabel="Retry pending completion synchronization"
              label="Retry pending completion"
              loading={manualRetrying}
              onPress={retryQueuedCompletion}
              variant="secondary"
            />
          ) : null}
          {quest.occurrence?.status === "completed" && quest.occurrence.activeCompletionId ? (
            <AppButton
              accessibilityHint="Opens an online-only confirmation to correct this completion while preserving history."
              label="Reverse completion"
              onPress={() => {
                reversalRequest.current = null;
                setReversalError(null);
                setReversalDialogVisible(true);
              }}
              variant="secondary"
            />
          ) : null}
          {quest.definitionState === "active" && quest.campaignStatus !== "archived" ? (
            <AppButton
              icon="pencil-outline"
              label="Edit quest"
              onPress={() => router.push(PROTECTED_ROUTES.questEdit(quest.id))}
            />
          ) : null}
          {quest.campaignStatus !== "archived" ? (
            quest.definitionState === "archived" ? (
              <AppButton
                label="Restore quest"
                loading={transitioning}
                onPress={() => {
                  if (transitioning) return;
                  restoreMutationId.current ??= questApi.createMutationId();
                  setTransitioning(true);
                  setTransitionError(null);
                  void questApi
                    .restore(quest.id, quest.recordVersion, restoreMutationId.current)
                    .then(() => {
                      invalidateCachedCampaign(ownerId, quest.campaignId);
                      AccessibilityInfo.announceForAccessibility("Quest restored.");
                      router.replace(PROTECTED_ROUTES.campaignDetail(quest.campaignId));
                    })
                    .catch((caught) => {
                      const message = caught instanceof QuestRequestError ? caught.message : "The quest lifecycle change failed.";
                      setTransitionError(message);
                      AccessibilityInfo.announceForAccessibility(message);
                    })
                    .finally(() => setTransitioning(false));
                }}
                variant="primary"
              />
            ) : (
              <AppButton
                label="Archive quest"
                onPress={() => {
                  archiveRequest.current = null;
                  setArchiveError(null);
                  setArchiveDialogVisible(true);
                }}
                variant="destructive"
              />
            )
          ) : (
            <AppText tone="muted">Restore the campaign before changing this quest.</AppText>
          )}
          {transitionError ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">{transitionError}</AppText>
            </View>
          ) : null}
          {refreshError ? (
            <View style={styles.snapshot}>
              <ErrorState kind="section" onRetry={() => void load("retry")} />
              <AppText accessibilityLiveRegion="assertive" tone="error">
                Quest refresh failed. {refreshError}
              </AppText>
            </View>
          ) : null}
          {refreshing && reduceMotion ? (
            <AppText accessibilityLiveRegion="polite" tone="muted" style={styles.center}>
              Refreshing quest…
            </AppText>
          ) : null}
          <AppButton
            label="View campaign"
            onPress={() => router.push(PROTECTED_ROUTES.campaignDetail(quest.campaignId))}
            variant="secondary"
          />
        </ScrollView>
      ) : null}
      {quest && archiveConfirmation && quest.definitionState === "active" && quest.campaignStatus !== "archived" ? (
        <AppDialog
          busy={transitioning}
          confirmLabel="Archive"
          description={archiveConfirmation.description}
          dismissLabel="Cancel"
          kind="destructive"
          onConfirm={archiveQuest}
          onDismiss={() => {
            if (archivePending.current) return;
            setArchiveDialogVisible(false);
            setArchiveError(null);
          }}
          title={archiveConfirmation.title}
          visible={archiveDialogVisible}
        >
          {archiveError ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">{archiveError}</AppText>
            </View>
          ) : null}
        </AppDialog>
      ) : null}
      {quest?.occurrence?.status === "completed" && quest.occurrence.activeCompletionId ? (
        <AppDialog
          busy={reversing}
          confirmLabel="Reverse completion"
          description="This online correction preserves the original completion and adds a reversal to its history."
          dismissLabel="Cancel"
          kind="destructive"
          onConfirm={reverseCompletion}
          onDismiss={() => {
            if (reversalPending.current) return;
            setReversalDialogVisible(false);
            setReversalError(null);
          }}
          title="Reverse this completion?"
          visible={reversalDialogVisible}
        >
          {reversalError ? (
            <View style={styles.snapshot}>
              <ErrorState kind="inline" />
              <AppText accessibilityLiveRegion="assertive" tone="error">{reversalError}</AppText>
            </View>
          ) : null}
        </AppDialog>
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

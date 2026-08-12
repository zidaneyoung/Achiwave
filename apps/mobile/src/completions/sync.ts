import NetInfo from "@react-native-community/netinfo";

import { AuthenticationRequestError, authenticationService } from "../auth/service";
import { invalidateCachedCampaign } from "../campaigns/cache";
import { completionApi } from "./api";
import { CompletionRequestError } from "./errors";
import { classifyCompletionFailure, type CompletionFailureReason } from "./failure";
import { confirmCompletionPresentation, failCompletionPresentation } from "./presentation";
import {
  COMPLETION_QUEUE_LEASE_MILLISECONDS,
} from "./queuePolicy";
import { completionQueueStorage } from "./queueStorage";
import { inputFromQueueRecord, type CompletionQueueRecord } from "./queueTypes";
import { nextCompletionRetryAt } from "./retryPolicy";
import { createSynchronizationEngine } from "./syncEngine";
import type { CompleteOccurrenceResult } from "./types";

const SYNC_BATCH_SIZE = 10;
const refreshListeners = new Set<(occurrenceId: string) => void>();
const manualRetryRuns = new Map<string, Promise<ManualRetryResult>>();

export type ManualRetryResult =
  | { outcome: "authentication_required" | "offline" | "not_eligible"; message: string }
  | { outcome: "succeeded" | "retryable_failure" | "permanent_failure"; message: string };

function isAuthenticationFailure(error: unknown): boolean {
  return error instanceof AuthenticationRequestError &&
    error.code === "session_rejected" ||
    error instanceof CompletionRequestError && error.code === "authentication";
}

function synchronizationFailure(error: unknown) {
  if (isAuthenticationFailure(error)) return { kind: "authentication" } as const;
  const failure = classifyCompletionFailure(error);
  if (failure.kind === "permanent_failure") {
    const current = error instanceof CompletionRequestError ? error.current : null;
    return {
      kind: "permanent" as const,
      safeClass: failure.reason,
      safeMessage: failure.message,
      canonicalResultJson: current ? JSON.stringify(current) : null,
    };
  }
  return {
    kind: "retryable" as const,
    safeClass: failure.reason,
    safeMessage: failure.message,
    retryAfterMilliseconds: error instanceof CompletionRequestError
      ? error.retryAfterMilliseconds
      : null,
  };
}

async function persistSynchronizedResult(
  operation: CompletionQueueRecord,
  result: CompleteOccurrenceResult,
): Promise<void> {
  await completionQueueStorage.markSucceeded(
    operation.accountId,
    operation.queueId,
    {
      completionId: result.completion.id,
      campaignId: result.campaign.id,
      eventSequence: Math.max(
        result.completion.eventSequence,
        ...result.progressEvents.map((event) => event.eventSequence),
      ),
      canonicalResultJson: JSON.stringify(result),
    },
    new Date(),
  );
}

async function presentSynchronizedResult(
  operation: CompletionQueueRecord,
  result: CompleteOccurrenceResult,
): Promise<void> {
  confirmCompletionPresentation(operation.accountId, result);
  invalidateCachedCampaign(operation.accountId, result.campaign.id);
  for (const listener of refreshListeners) listener(result.occurrence.id);
}

async function persistRetryableResult(
  operation: CompletionQueueRecord,
  failure: {
    safeClass: string;
    safeMessage: string;
    retryAfterMilliseconds: number | null;
  },
): Promise<void> {
  await completionQueueStorage.markRetryableFailure(
    operation.accountId,
    operation.queueId,
    failure.safeClass,
    failure.safeMessage,
    nextCompletionRetryAt(
      operation.automaticAttemptCount,
      failure.retryAfterMilliseconds,
    ),
    new Date(),
  );
}

async function persistPermanentResult(
  operation: CompletionQueueRecord,
  failure: {
    safeClass: string;
    safeMessage: string;
    canonicalResultJson: string | null;
  },
): Promise<void> {
  await completionQueueStorage.markPermanentFailure(
    operation.accountId,
    operation.queueId,
    failure.safeClass,
    failure.safeMessage,
    failure.canonicalResultJson,
    new Date(),
  );
  failCompletionPresentation(
    operation.accountId,
    operation.occurrenceId,
    operation.clientMutationId,
    {
      reason: failure.safeClass as CompletionFailureReason,
      kind: "permanent_failure",
      message: failure.safeMessage,
      nextAction: "Review the latest state",
      refreshCanonical: true,
    },
  );
  const current = failure.canonicalResultJson
    ? JSON.parse(failure.canonicalResultJson) as { campaign?: { id?: unknown } }
    : null;
  if (typeof current?.campaign?.id === "string") {
    invalidateCachedCampaign(operation.accountId, current.campaign.id);
  }
  for (const listener of refreshListeners) listener(operation.occurrenceId);
}

const engine = createSynchronizationEngine<
  CompletionQueueRecord,
  CompleteOccurrenceResult
>({
  async validateSession(accountId) {
    const context = await authenticationService.revalidateCurrentSession();
    if (context.accountId !== accountId) {
      throw new AuthenticationRequestError(
        "session_rejected",
        "The synchronization account no longer matches this session.",
      );
    }
  },
  leaseDue(accountId) {
    return completionQueueStorage.leaseDueBatch(
      accountId,
      new Date(),
      COMPLETION_QUEUE_LEASE_MILLISECONDS,
      SYNC_BATCH_SIZE,
    );
  },
  submit(operation) {
    return completionApi.complete(inputFromQueueRecord(operation));
  },
  persistSuccess(operation, result) {
    return persistSynchronizedResult(operation, result);
  },
  async afterPersistedSuccess(operation, result) {
    await presentSynchronizedResult(operation, result);
  },
  classifyFailure(error) {
    return synchronizationFailure(error);
  },
  persistRetryableFailure(operation, failure) {
    return persistRetryableResult(operation, failure);
  },
  async persistPermanentFailure(operation, failure) {
    await persistPermanentResult(operation, failure);
  },
  releaseLeases(accountId, operations) {
    return completionQueueStorage.releaseLeases(
      accountId,
      operations.map((operation) => operation.queueId),
      new Date(),
    );
  },
});

export function synchronizeCompletionQueue(accountId: string) {
  return engine.run(accountId);
}

async function executeManualRetry(
  accountId: string,
  queueId: string,
): Promise<ManualRetryResult> {
  const network = await NetInfo.fetch();
  if (network.isConnected !== true || network.isInternetReachable === false) {
    return { outcome: "offline", message: "Reconnect before retrying this completion." };
  }
  try {
    const context = await authenticationService.revalidateCurrentSession();
    if (context.accountId !== accountId) {
      return { outcome: "authentication_required", message: "Sign in to the matching account before retrying." };
    }
  } catch (error) {
    return {
      outcome: isAuthenticationFailure(error) ? "authentication_required" : "offline",
      message: isAuthenticationFailure(error)
        ? "Sign in again before retrying this completion."
        : "The session could not be checked. Reconnect and try again.",
    };
  }
  const operation = await completionQueueStorage.leaseManualRetry(
    accountId,
    queueId,
    new Date(),
    COMPLETION_QUEUE_LEASE_MILLISECONDS,
  );
  if (!operation) {
    return { outcome: "not_eligible", message: "This completion is not eligible for manual retry." };
  }
  try {
    const result = await completionApi.complete(inputFromQueueRecord(operation));
    await persistSynchronizedResult(operation, result);
    await presentSynchronizedResult(operation, result);
    return { outcome: "succeeded", message: "Completion synchronized with the server." };
  } catch (error) {
    const failure = synchronizationFailure(error);
    if (failure.kind === "authentication") {
      await completionQueueStorage.releaseManualLease(accountId, queueId, new Date());
      return { outcome: "authentication_required", message: "Sign in again before retrying this completion." };
    }
    if (failure.kind === "permanent") {
      await persistPermanentResult(operation, failure);
      return { outcome: "permanent_failure", message: failure.safeMessage };
    }
    await persistRetryableResult(operation, failure);
    return { outcome: "retryable_failure", message: failure.safeMessage };
  }
}

export function manuallyRetryCompletion(
  accountId: string,
  queueId: string,
): Promise<ManualRetryResult> {
  const key = `${accountId}:${queueId}`;
  const existing = manualRetryRuns.get(key);
  if (existing) return existing;
  const run = executeManualRetry(accountId, queueId).finally(() => {
    if (manualRetryRuns.get(key) === run) manualRetryRuns.delete(key);
  });
  manualRetryRuns.set(key, run);
  return run;
}

export function subscribeCompletionRefresh(
  listener: (occurrenceId: string) => void,
): () => void {
  refreshListeners.add(listener);
  return () => refreshListeners.delete(listener);
}

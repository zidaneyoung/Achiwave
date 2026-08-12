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
import { createSynchronizationEngine } from "./syncEngine";
import type { CompleteOccurrenceResult } from "./types";

const SYNC_BATCH_SIZE = 10;
const refreshListeners = new Set<(occurrenceId: string) => void>();

function isAuthenticationFailure(error: unknown): boolean {
  return error instanceof AuthenticationRequestError &&
    error.code === "session_rejected" ||
    error instanceof CompletionRequestError && error.code === "authentication";
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
    return completionQueueStorage.markSucceeded(
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
  },
  async afterPersistedSuccess(operation, result) {
    confirmCompletionPresentation(operation.accountId, result);
    invalidateCachedCampaign(operation.accountId, result.campaign.id);
    for (const listener of refreshListeners) listener(result.occurrence.id);
  },
  classifyFailure(error) {
    if (isAuthenticationFailure(error)) return { kind: "authentication" };
    const failure = classifyCompletionFailure(error);
    if (failure.kind === "permanent_failure") {
      const current = error instanceof CompletionRequestError ? error.current : null;
      return {
        kind: "permanent",
        safeClass: failure.reason,
        safeMessage: failure.message,
        canonicalResultJson: current ? JSON.stringify(current) : null,
      };
    }
    return { kind: "retryable", safeClass: failure.reason, safeMessage: failure.message };
  },
  persistRetryableFailure(operation, failure) {
    return completionQueueStorage.markRetryableFailure(
      operation.accountId,
      operation.queueId,
      failure.safeClass,
      failure.safeMessage,
      new Date(),
    );
  },
  async persistPermanentFailure(operation, failure) {
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

export function subscribeCompletionRefresh(
  listener: (occurrenceId: string) => void,
): () => void {
  refreshListeners.add(listener);
  return () => refreshListeners.delete(listener);
}

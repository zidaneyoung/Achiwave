import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import type { CompleteOccurrenceInput } from "./api";
import { canonicalCompletionPayload } from "./queuePolicy";
import {
  completionQueueStorage,
  subscribeCompletionQueueRecord,
} from "./queueStorage";
import type { CompletionQueueRecord } from "./queueTypes";

export const completionQueue = {
  initialize(accountId: string): Promise<CompletionQueueRecord[]> {
    return completionQueueStorage.initializePartition(accountId);
  },

  pendingCount(accountId: string): Promise<number> {
    return completionQueueStorage.countPending(accountId);
  },

  nextDueAt(accountId: string): Promise<string | null> {
    return completionQueueStorage.nextDueAt(accountId);
  },

  dismissPermanentFailure(accountId: string, queueId: string): Promise<boolean> {
    return completionQueueStorage.dismissPermanentFailure(accountId, queueId);
  },

  latest(
    accountId: string,
    occurrenceId: string,
  ): Promise<CompletionQueueRecord | null> {
    return completionQueueStorage.findLatest(accountId, occurrenceId);
  },

  subscribe(
    accountId: string,
    occurrenceId: string,
    listener: () => void,
  ): () => void {
    return subscribeCompletionQueueRecord(accountId, occurrenceId, listener);
  },

  async enqueue(
    authenticatedAccountId: string,
    input: CompleteOccurrenceInput,
  ): Promise<{ record: CompletionQueueRecord; reused: boolean }> {
    const context = await authenticationService.getCurrentDeviceContext();
    if (context.accountId !== authenticatedAccountId) {
      throw new Error("The completion queue account does not match the session.");
    }
    const existing = await completionQueueStorage.findActive(
      context.accountId,
      input.occurrenceId,
    );
    if (existing) return { record: existing, reused: true };

    const canonicalPayloadHash = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      canonicalCompletionPayload(input),
    );
    const now = new Date().toISOString();
    try {
      const record = await completionQueueStorage.insert({
        queueId: Crypto.randomUUID(),
        accountId: context.accountId,
        deviceId: context.deviceId,
        occurrenceId: input.occurrenceId,
        expectedOccurrenceVersion: input.expectedOccurrenceVersion,
        clientMutationId: input.clientMutationId,
        canonicalPayloadHash,
        deviceObservedAt: input.deviceObservedAt,
        deviceTimezoneName: input.deviceTimezoneName,
        now,
      });
      return { record, reused: false };
    } catch (error) {
      const raced = await completionQueueStorage.findActive(
        context.accountId,
        input.occurrenceId,
      );
      if (raced) return { record: raced, reused: true };
      throw error;
    }
  },

  purge(): Promise<void> {
    return completionQueueStorage.purgeAll();
  },
};

import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import type { CompleteOccurrenceInput } from "./api";
import { canonicalCompletionPayload } from "./queuePolicy";
import { completionQueueStorage } from "./queueStorage";
import type { CompletionQueueRecord } from "./queueTypes";

export const completionQueue = {
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
};

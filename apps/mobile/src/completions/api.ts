import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import { AuthenticationRequestError } from "../auth/service";
import { isObject, parseCompleteOccurrence, parseReverseCompletion } from "./contracts";
import type { CompleteOccurrenceResult, ReverseCompletionResult } from "./types";
import { CompletionRequestError } from "./errors";
export { CompletionRequestError } from "./errors";

export interface CompleteOccurrenceInput {
  occurrenceId: string;
  expectedOccurrenceVersion: number;
  clientMutationId: string;
  deviceObservedAt: string;
  deviceTimezoneName: string;
}

async function readJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch { return null; }
}

function responseError(response: Response, body: unknown): CompletionRequestError {
  const serverCode = isObject(body) && typeof body.code === "string" ? body.code : null;
  const current = isObject(body) && isObject(body.current) ? body.current : null;
  if (response.status === 404) {
    return new CompletionRequestError("not_found", "This occurrence is no longer available.", serverCode);
  }
  if (response.status === 409) {
    return new CompletionRequestError(
      "conflict",
      serverCode === "stale_occurrence_version"
        ? "This occurrence changed elsewhere. Refresh before trying again."
        : serverCode === "occurrence_not_eligible"
          ? "This occurrence is not eligible for completion."
          : "This completion conflicts with newer server data.",
      serverCode,
      current,
    );
  }
  if (response.status === 422) {
    return new CompletionRequestError("validation", "The completion request is invalid.", serverCode);
  }
  return new CompletionRequestError("server", "The completion could not be confirmed. Try again.", serverCode);
}

export const completionApi = {
  createMutationId(): string { return Crypto.randomUUID(); },

  async complete(input: CompleteOccurrenceInput): Promise<CompleteOccurrenceResult> {
    try {
      const response = await authenticationService.request(
        `/api/v1/quest-occurrences/${encodeURIComponent(input.occurrenceId)}/complete`,
        {
          body: JSON.stringify({
            client_mutation_id: input.clientMutationId,
            expected_occurrence_version: input.expectedOccurrenceVersion,
            device_observed_at: input.deviceObservedAt,
            device_timezone_name: input.deviceTimezoneName,
          }),
          headers: { "Content-Type": "application/json" },
          method: "POST",
        },
      );
      const body = await readJson(response);
      if (!response.ok) throw responseError(response, body);
      const result = parseCompleteOccurrence(body);
      if (!result) {
        throw new CompletionRequestError("invalid_response", "Completion confirmation is temporarily unavailable.");
      }
      return result;
    } catch (error) {
      if (error instanceof CompletionRequestError) throw error;
      if (error instanceof AuthenticationRequestError) {
        if (error.code === "session_rejected") {
          throw new CompletionRequestError(
            "authentication",
            "Your session ended. Sign in again before completing this quest.",
          );
        }
        if (error.code === "unavailable") {
          throw new CompletionRequestError("offline", "Reconnect to complete this quest.");
        }
      }
      throw new CompletionRequestError("offline", "Reconnect to complete this quest.");
    }
  },

  async reverse(input: {
    completionId: string;
    expectedOccurrenceVersion: number;
    clientMutationId: string;
  }): Promise<ReverseCompletionResult> {
    try {
      const response = await authenticationService.request(
        `/api/v1/quest-completions/${encodeURIComponent(input.completionId)}/reverse`,
        {
          body: JSON.stringify({
            client_mutation_id: input.clientMutationId,
            expected_occurrence_version: input.expectedOccurrenceVersion,
            reason: "user_correction",
          }),
          headers: { "Content-Type": "application/json" },
          method: "POST",
        },
      );
      const body = await readJson(response);
      if (!response.ok) throw responseError(response, body);
      const result = parseReverseCompletion(body);
      if (!result) {
        throw new CompletionRequestError("invalid_response", "Reversal confirmation is temporarily unavailable.");
      }
      return result;
    } catch (error) {
      if (error instanceof CompletionRequestError) throw error;
      throw new CompletionRequestError("offline", "Reversal requires an online connection.");
    }
  },
};

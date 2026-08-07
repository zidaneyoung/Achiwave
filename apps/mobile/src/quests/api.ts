import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import { isObject, parseCampaign } from "../campaigns/contracts";
import type { Campaign } from "../campaigns/types";
import { parseQuest } from "./contracts";
import type { Quest } from "./types";

export class QuestRequestError extends Error {
  constructor(
    public readonly code: "conflict" | "invalid_response" | "not_found" | "offline" | "server" | "validation",
    message: string,
    public readonly currentCampaign: Campaign | null = null,
  ) {
    super(message);
    this.name = "QuestRequestError";
  }
}

async function readJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch { return null; }
}

function responseError(response: Response, body: unknown): QuestRequestError {
  if (response.status === 409) {
    const currentCampaign = isObject(body) && "current" in body ? parseCampaign(body.current) : null;
    return new QuestRequestError(
      "conflict",
      currentCampaign
        ? "Campaign data changed elsewhere. Refresh before creating the quest."
        : "This submission conflicts with newer server data.",
      currentCampaign,
    );
  }
  if (response.status === 404) return new QuestRequestError("not_found", "This campaign cannot accept new quests.");
  if (response.status === 422) return new QuestRequestError("validation", "Check the quest details and try again.");
  return new QuestRequestError("server", "The quest could not be saved. Try again.");
}

export const questApi = {
  createMutationId(): string { return Crypto.randomUUID(); },

  async createOneTime(input: {
    campaignId: string;
    campaignRecordVersion: number;
    title: string;
    rewardXp: number;
    clientMutationId: string;
  }): Promise<Quest> {
    try {
      const response = await authenticationService.request(
        `/api/v1/campaigns/${encodeURIComponent(input.campaignId)}/quests`,
        {
          body: JSON.stringify({
            title: input.title,
            reward_xp: input.rewardXp,
            campaign_record_version: input.campaignRecordVersion,
            client_mutation_id: input.clientMutationId,
          }),
          headers: { "Content-Type": "application/json" },
          method: "POST",
        },
      );
      const body = await readJson(response);
      if (!response.ok) throw responseError(response, body);
      const quest = parseQuest(body);
      if (!quest) throw new QuestRequestError("invalid_response", "Quest data is temporarily unavailable.");
      return quest;
    } catch (error) {
      if (error instanceof QuestRequestError) throw error;
      throw new QuestRequestError("offline", "Reconnect before creating this quest.");
    }
  },
};

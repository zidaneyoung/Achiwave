import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import { isObject, parseCampaign } from "../campaigns/contracts";
import type { Campaign } from "../campaigns/types";
import { parseQuest, parseQuestAuthoringOptions } from "./contracts";
import type { Quest, QuestAuthoringOptions, QuestCategory } from "./types";

export class QuestRequestError extends Error {
  constructor(
    public readonly code: "conflict" | "invalid_response" | "not_found" | "offline" | "server" | "validation",
    message: string,
    public readonly currentCampaign: Campaign | null = null,
    public readonly currentQuest: Quest | null = null,
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
    const currentQuest = isObject(body) && "current" in body ? parseQuest(body.current) : null;
    return new QuestRequestError(
      "conflict",
      currentCampaign
        ? "Campaign data changed elsewhere. Refresh before creating the quest."
        : currentQuest
          ? "Quest data changed elsewhere. Refresh before saving again."
          : "This submission conflicts with newer server data.",
      currentCampaign,
      currentQuest,
    );
  }
  if (response.status === 404) return new QuestRequestError("not_found", "This quest or campaign is unavailable.");
  if (response.status === 422) return new QuestRequestError("validation", "Check the quest details and try again.");
  return new QuestRequestError("server", "The quest could not be saved. Try again.");
}

async function requestQuest(path: string, init?: RequestInit): Promise<Quest> {
  try {
    const response = await authenticationService.request(path, init);
    const body = await readJson(response);
    if (!response.ok) throw responseError(response, body);
    const quest = parseQuest(body);
    if (!quest) throw new QuestRequestError("invalid_response", "Quest data is temporarily unavailable.");
    return quest;
  } catch (error) {
    if (error instanceof QuestRequestError) throw error;
    throw new QuestRequestError("offline", "Reconnect to load or save this quest.");
  }
}

async function requestAuthoringOptions(): Promise<QuestAuthoringOptions> {
  try {
    const response = await authenticationService.request("/api/v1/quests/authoring-options");
    const body = await readJson(response);
    if (!response.ok) throw responseError(response, body);
    const options = parseQuestAuthoringOptions(body);
    if (!options) throw new QuestRequestError("invalid_response", "Quest choices are temporarily unavailable.");
    return options;
  } catch (error) {
    if (error instanceof QuestRequestError) throw error;
    throw new QuestRequestError("offline", "Reconnect to load quest choices.");
  }
}

export const questApi = {
  createMutationId(): string { return Crypto.randomUUID(); },

  getAuthoringOptions(): Promise<QuestAuthoringOptions> {
    return requestAuthoringOptions();
  },

  async createOneTime(input: {
    campaignId: string;
    campaignRecordVersion: number;
    title: string;
    description: string | null;
    category: QuestCategory | null;
    rewardXp: number;
    dueLocalDateTime: string | null;
    clientMutationId: string;
  }): Promise<Quest> {
    return requestQuest(
      `/api/v1/campaigns/${encodeURIComponent(input.campaignId)}/quests`,
      {
        body: JSON.stringify({
          title: input.title,
          description: input.description,
          category: input.category,
          reward_xp: input.rewardXp,
          due_local_datetime: input.dueLocalDateTime,
          campaign_record_version: input.campaignRecordVersion,
          client_mutation_id: input.clientMutationId,
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      },
    );
  },

  get(questId: string): Promise<Quest> {
    return requestQuest(`/api/v1/quests/${encodeURIComponent(questId)}`);
  },

  update(
    questId: string,
    input: {
      title: string;
      description: string | null;
      category: QuestCategory | null;
      rewardXp: number;
      recordVersion: number;
      clientMutationId: string;
    },
  ): Promise<Quest> {
    return requestQuest(`/api/v1/quests/${encodeURIComponent(questId)}`, {
      body: JSON.stringify({
        title: input.title,
        description: input.description,
        category: input.category,
        reward_xp: input.rewardXp,
        record_version: input.recordVersion,
        client_mutation_id: input.clientMutationId,
      }),
      headers: { "Content-Type": "application/json" },
      method: "PATCH",
    });
  },

  archive(questId: string, recordVersion: number, clientMutationId: string): Promise<Quest> {
    return requestQuest(`/api/v1/quests/${encodeURIComponent(questId)}/archive`, {
      body: JSON.stringify({
        record_version: recordVersion,
        client_mutation_id: clientMutationId,
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  },

  restore(questId: string, recordVersion: number, clientMutationId: string): Promise<Quest> {
    return requestQuest(`/api/v1/quests/${encodeURIComponent(questId)}/restore`, {
      body: JSON.stringify({
        record_version: recordVersion,
        client_mutation_id: clientMutationId,
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  },
};

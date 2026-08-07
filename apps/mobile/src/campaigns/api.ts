import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import {
  isObject,
  parseCampaign,
  parseCampaignDetail,
  parseCampaignList,
} from "./contracts";
import type {
  Campaign,
  CampaignDetail,
  CampaignListPage,
  CampaignListView,
} from "./types";

export type CampaignRequestErrorCode =
  | "conflict"
  | "invalid_response"
  | "not_found"
  | "offline"
  | "server"
  | "validation";

export class CampaignRequestError extends Error {
  constructor(
    public readonly code: CampaignRequestErrorCode,
    message: string,
    public readonly currentCampaign: Campaign | null = null,
  ) {
    super(message);
    this.name = "CampaignRequestError";
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function errorFromResponse(response: Response, body: unknown): CampaignRequestError {
  const code = isObject(body) && typeof body.code === "string" ? body.code : null;
  if (response.status === 409) {
    const currentCampaign =
      isObject(body) && "current" in body ? parseCampaign(body.current) : null;
    return new CampaignRequestError(
      "conflict",
      code === "client_mutation_conflict"
        ? "This submission was already used for different campaign details."
        : "Campaign data changed elsewhere. Refresh before trying again.",
      currentCampaign,
    );
  }
  if (response.status === 404) {
    return new CampaignRequestError("not_found", "This campaign is unavailable.");
  }
  if (response.status === 422) {
    return new CampaignRequestError(
      "validation",
      "Check the campaign details and try again.",
    );
  }
  return new CampaignRequestError(
    "server",
    "The campaign could not be saved. Try again.",
  );
}

async function campaignResponse(response: Response): Promise<Campaign> {
  const body = await readJson(response);
  if (!response.ok) throw errorFromResponse(response, body);
  const campaign = parseCampaign(body);
  if (!campaign) {
    throw new CampaignRequestError(
      "invalid_response",
      "Campaign data is temporarily unavailable.",
    );
  }
  return campaign;
}

async function requestCampaign(path: string, init?: RequestInit): Promise<Campaign> {
  try {
    const response = await authenticationService.request(path, init);
    return await campaignResponse(response);
  } catch (error) {
    if (error instanceof CampaignRequestError) throw error;
    throw new CampaignRequestError(
      "offline",
      "Reconnect before saving campaign changes.",
    );
  }
}

async function requestCampaignList(view: CampaignListView): Promise<CampaignListPage> {
  try {
    const response = await authenticationService.request(
      `/api/v1/campaigns?view=${view}&limit=100`,
    );
    const body = await readJson(response);
    if (!response.ok) throw errorFromResponse(response, body);
    const page = parseCampaignList(body);
    if (!page) {
      throw new CampaignRequestError(
        "invalid_response",
        "Campaign data is temporarily unavailable.",
      );
    }
    return page;
  } catch (error) {
    if (error instanceof CampaignRequestError) throw error;
    throw new CampaignRequestError(
      "offline",
      "Reconnect to refresh campaigns.",
    );
  }
}

async function requestCampaignDetail(
  campaignId: string,
  includeArchivedQuests: boolean,
): Promise<CampaignDetail> {
  try {
    const suffix = includeArchivedQuests ? "?include_archived_quests=true" : "";
    const response = await authenticationService.request(
      `/api/v1/campaigns/${encodeURIComponent(campaignId)}${suffix}`,
    );
    const body = await readJson(response);
    if (!response.ok) throw errorFromResponse(response, body);
    const detail = parseCampaignDetail(body);
    if (!detail) {
      throw new CampaignRequestError(
        "invalid_response",
        "Campaign data is temporarily unavailable.",
      );
    }
    return detail;
  } catch (error) {
    if (error instanceof CampaignRequestError) throw error;
    throw new CampaignRequestError(
      "offline",
      "Reconnect to refresh this campaign.",
    );
  }
}

export const campaignApi = {
  createMutationId(): string {
    return Crypto.randomUUID();
  },

  create(input: {
    title: string;
    description: string | null;
    clientMutationId: string;
  }): Promise<Campaign> {
    return requestCampaign("/api/v1/campaigns", {
      body: JSON.stringify({
        title: input.title,
        description: input.description,
        client_mutation_id: input.clientMutationId,
      }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  },

  update(
    campaignId: string,
    input: {
      title: string;
      description: string | null;
      recordVersion: number;
      clientMutationId: string;
    },
  ): Promise<Campaign> {
    return requestCampaign(`/api/v1/campaigns/${encodeURIComponent(campaignId)}`, {
      body: JSON.stringify({
        title: input.title,
        description: input.description,
        record_version: input.recordVersion,
        client_mutation_id: input.clientMutationId,
      }),
      headers: { "Content-Type": "application/json" },
      method: "PATCH",
    });
  },

  archive(
    campaignId: string,
    recordVersion: number,
    clientMutationId: string,
  ): Promise<Campaign> {
    return requestCampaign(
      `/api/v1/campaigns/${encodeURIComponent(campaignId)}/archive`,
      {
        body: JSON.stringify({
          record_version: recordVersion,
          client_mutation_id: clientMutationId,
        }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      },
    );
  },

  list(view: CampaignListView): Promise<CampaignListPage> {
    return requestCampaignList(view);
  },

  get(campaignId: string, includeArchivedQuests = false): Promise<CampaignDetail> {
    return requestCampaignDetail(campaignId, includeArchivedQuests);
  },
};

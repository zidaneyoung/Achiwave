import * as Crypto from "expo-crypto";

import { authenticationService } from "../auth/service";
import { isObject, parseCampaign } from "./contracts";
import type { Campaign } from "./types";

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
    return new CampaignRequestError(
      "conflict",
      code === "client_mutation_conflict"
        ? "This submission was already used for different campaign details."
        : "Campaign data changed elsewhere. Refresh before trying again.",
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
};

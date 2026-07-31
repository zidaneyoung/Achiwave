import {
  resolvePublicEnvironment,
  type PublicEnvironment,
} from "../config/environment";

export interface LivenessResponse {
  status: "ok";
}

export type ApiErrorCode = "unavailable" | "unexpected_response";

export class ApiRequestError extends Error {
  constructor(
    public readonly code: ApiErrorCode,
    message: string,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export interface ApiClient {
  getLiveness(): Promise<LivenessResponse>;
}

export function createApiClient(
  environment: PublicEnvironment = resolvePublicEnvironment(),
  fetchImplementation: typeof fetch = fetch,
  timeoutMilliseconds = 5_000,
): ApiClient {
  return {
    async getLiveness(): Promise<LivenessResponse> {
      const controller = new AbortController();
      const timeout = setTimeout(
        () => controller.abort(),
        timeoutMilliseconds,
      );

      let response: Response;
      try {
        response = await fetchImplementation(
          `${environment.apiBaseUrl}/health/live`,
          {
            headers: {
              Accept: "application/json",
            },
            method: "GET",
            signal: controller.signal,
          },
        );
      } catch {
        throw new ApiRequestError(
          "unavailable",
          "The Achiwave API is unavailable.",
        );
      } finally {
        clearTimeout(timeout);
      }

      if (!response.ok) {
        throw new ApiRequestError(
          "unexpected_response",
          "The Achiwave API returned an unexpected response.",
        );
      }

      let payload: unknown;
      try {
        payload = await response.json();
      } catch {
        throw new ApiRequestError(
          "unexpected_response",
          "The Achiwave API returned an unexpected response.",
        );
      }

      if (
        typeof payload !== "object" ||
        payload === null ||
        !("status" in payload) ||
        payload.status !== "ok"
      ) {
        throw new ApiRequestError(
          "unexpected_response",
          "The Achiwave API returned an unexpected response.",
        );
      }

      return { status: "ok" };
    },
  };
}

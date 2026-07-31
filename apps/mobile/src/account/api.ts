import { authenticationService } from "../auth/service";

export class AccountRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AccountRequestError";
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export const accountApi = {
  async deactivate(password: string): Promise<void> {
    const response = await authenticationService.request(
      "/api/v1/account/deactivate",
      {
        body: JSON.stringify({ password }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      },
    );
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new AccountRequestError("Account deactivation could not be completed.");
    }
    if (!response.ok) {
      if (isObject(body) && body.code === "invalid_credentials") {
        throw new AccountRequestError("The password was not accepted.");
      }
      throw new AccountRequestError("Account deactivation could not be completed.");
    }
    if (!isObject(body) || body.account_state !== "deactivated") {
      throw new AccountRequestError("Account deactivation could not be confirmed.");
    }
    await authenticationService.handleAccountDeactivated();
  },
};

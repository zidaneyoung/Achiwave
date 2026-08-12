export type CompletionErrorCode =
  | "authentication"
  | "conflict"
  | "invalid_response"
  | "not_found"
  | "offline"
  | "server"
  | "validation";

export class CompletionRequestError extends Error {
  readonly code: CompletionErrorCode;
  readonly serverCode: string | null;
  readonly current: Record<string, unknown> | null;

  constructor(
    code: CompletionErrorCode,
    message: string,
    serverCode: string | null = null,
    current: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = "CompletionRequestError";
    this.code = code;
    this.serverCode = serverCode;
    this.current = current;
  }
}

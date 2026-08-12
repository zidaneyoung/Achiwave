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
  readonly current: CompletionConflictSnapshot | null;

  constructor(
    code: CompletionErrorCode,
    message: string,
    serverCode: string | null = null,
    current: CompletionConflictSnapshot | null = null,
  ) {
    super(message);
    this.name = "CompletionRequestError";
    this.code = code;
    this.serverCode = serverCode;
    this.current = current;
  }
}
import type { CompletionConflictSnapshot } from "./conflicts";

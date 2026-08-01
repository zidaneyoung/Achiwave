/**
 * Native stacks own Android back. Tab history is consulted only when no modal or
 * stack screen can pop, then falls back to Home before Android may exit.
 */
export const AUTHENTICATED_TAB_BACK_BEHAVIOR = "history" as const;

export const AUTHENTICATED_TAB_INITIAL_ROUTE = "home" as const;

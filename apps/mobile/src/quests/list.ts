import type { QuestListFilters, QuestListStatus } from "./types";

export const QUEST_LIST_PAGE_SIZE = 50;

export interface CombinedQuestListPages<TItem extends { id: string }> {
  items: TItem[];
  nextOffset: number;
  total: number;
}

export function combineQuestListPages<TItem extends { id: string }>(
  pages: ReadonlyArray<{
    items: readonly TItem[];
    offset: number;
    total: number;
  }>,
): CombinedQuestListPages<TItem> {
  const items = new Map<string, TItem>();
  let nextOffset = 0;
  let total = 0;
  for (const page of pages) {
    if (page.offset !== nextOffset) {
      throw new RangeError("Quest list refresh pages must be contiguous.");
    }
    for (const item of page.items) items.set(item.id, item);
    total = page.total;
    nextOffset = page.items.length === 0
      ? page.total
      : page.offset + page.items.length;
  }
  return { items: [...items.values()], nextOffset, total };
}

export const QUEST_LIST_STATUS_OPTIONS: ReadonlyArray<{
  value: QuestListStatus;
  label: string;
}> = [
  { value: "active", label: "Active" },
  { value: "scheduled", label: "Scheduled" },
  { value: "available", label: "Available" },
  { value: "completed", label: "Completed" },
  { value: "reversed", label: "Reversed" },
  { value: "expired", label: "Expired" },
  { value: "voided", label: "Voided" },
  { value: "archived", label: "Archived" },
];

export interface QuestListDateErrors {
  dueFrom: string | null;
  dueTo: string | null;
}

export function createEmptyQuestListFilters(): QuestListFilters {
  return {
    campaignId: null,
    status: null,
    category: null,
    dueFrom: "",
    dueTo: "",
  };
}

export function countQuestListFilters(filters: QuestListFilters): number {
  return [
    filters.campaignId,
    filters.status,
    filters.category,
    filters.dueFrom.trim(),
    filters.dueTo.trim(),
  ].filter((value) => value !== null && value !== "").length;
}

function isCalendarDate(value: string): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/u.exec(value);
  if (!match) return false;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1) return false;
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return day <= daysInMonth[month - 1];
}

export function validateQuestListDates(
  filters: Pick<QuestListFilters, "dueFrom" | "dueTo">,
): QuestListDateErrors {
  const dueFrom = filters.dueFrom.trim();
  const dueTo = filters.dueTo.trim();
  const dueFromError = dueFrom && !isCalendarDate(dueFrom)
    ? "Enter the start date as YYYY-MM-DD."
    : null;
  let dueToError = dueTo && !isCalendarDate(dueTo)
    ? "Enter the end date as YYYY-MM-DD."
    : null;
  if (!dueFromError && !dueToError && dueFrom && dueTo && dueFrom > dueTo) {
    dueToError = "End date must be on or after the start date.";
  }
  return { dueFrom: dueFromError, dueTo: dueToError };
}

export function buildQuestListPath(
  filters: QuestListFilters,
  limit = QUEST_LIST_PAGE_SIZE,
  offset = 0,
): string {
  if (!Number.isInteger(limit) || limit < 1 || !Number.isInteger(offset) || offset < 0) {
    throw new RangeError("Quest list pagination must use a positive limit and nonnegative offset.");
  }
  const values: Array<[string, string]> = [];
  if (filters.campaignId) values.push(["campaign_id", filters.campaignId]);
  if (filters.status) values.push(["status", filters.status]);
  if (filters.category) values.push(["category", filters.category]);
  if (filters.dueFrom.trim()) values.push(["due_from", filters.dueFrom.trim()]);
  if (filters.dueTo.trim()) values.push(["due_to", filters.dueTo.trim()]);
  values.push(["limit", String(limit)], ["offset", String(offset)]);
  const query = values
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join("&");
  return `/api/v1/quests?${query}`;
}

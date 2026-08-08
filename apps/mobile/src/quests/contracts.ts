import type {
  OneTimeOccurrence,
  Quest,
  QuestAuthoringOptions,
  QuestCategory,
} from "./types";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return typeof value === "string" ? value : undefined;
}

function nonnegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

export function isQuestCategory(value: unknown): value is QuestCategory {
  return (
    value === "personal" ||
    value === "health" ||
    value === "learning" ||
    value === "work" ||
    value === "finance"
  );
}

export function parseQuestAuthoringOptions(value: unknown): QuestAuthoringOptions | null {
  if (!isObject(value) || !Array.isArray(value.categories)) return null;
  const categories = value.categories.map((option) => {
    if (
      !isObject(option) ||
      !isQuestCategory(option.value) ||
      typeof option.label !== "string" ||
      option.label.length === 0
    ) return null;
    return { value: option.value, label: option.label };
  });
  if (categories.some((option) => option === null) || categories.length === 0) return null;
  return { categories: categories as QuestAuthoringOptions["categories"] };
}

function isOccurrenceStatus(
  value: unknown,
): value is OneTimeOccurrence["status"] {
  return (
    value === "scheduled" ||
    value === "available" ||
    value === "completed" ||
    value === "reversed" ||
    value === "expired" ||
    value === "voided"
  );
}

function parseOccurrence(value: unknown): OneTimeOccurrence | null {
  if (!isObject(value)) return null;
  const eligibilityExpiresAt = nullableString(value.eligibility_expires_at);
  if (
    typeof value.id !== "string" ||
    !isOccurrenceStatus(value.status) ||
    typeof value.occurrence_local_date !== "string" ||
    typeof value.timezone_name !== "string" ||
    typeof value.available_at !== "string" ||
    eligibilityExpiresAt === undefined ||
    !nonnegativeInteger(value.reward_xp) ||
    !nonnegativeInteger(value.record_version) ||
    value.record_version < 1
  ) return null;
  return {
    id: value.id,
    status: value.status,
    occurrenceLocalDate: value.occurrence_local_date,
    timezoneName: value.timezone_name,
    availableAt: value.available_at,
    eligibilityExpiresAt,
    rewardXp: value.reward_xp,
    recordVersion: value.record_version,
  };
}

export function parseQuest(value: unknown): Quest | null {
  if (!isObject(value)) return null;
  const description = nullableString(value.description);
  const category = value.category === null ? null : isQuestCategory(value.category) ? value.category : undefined;
  const availableFrom = nullableString(value.available_from);
  const dueAt = nullableString(value.due_at);
  const timezoneName = nullableString(value.timezone_name);
  const archivedAt = nullableString(value.archived_at);
  const restoredAt = nullableString(value.restored_at);
  const occurrence = value.occurrence === null ? null : parseOccurrence(value.occurrence);
  if (
    typeof value.id !== "string" ||
    typeof value.campaign_id !== "string" ||
    !nonnegativeInteger(value.campaign_record_version) ||
    value.campaign_record_version < 1 ||
    (value.campaign_status !== "active" && value.campaign_status !== "completed" && value.campaign_status !== "archived") ||
    (value.quest_type !== "one_time" && value.quest_type !== "recurring") ||
    (value.definition_state !== "active" && value.definition_state !== "archived") ||
    typeof value.title !== "string" ||
    description === undefined ||
    category === undefined ||
    typeof value.category_label !== "string" ||
    value.category_label.length === 0 ||
    !nonnegativeInteger(value.reward_xp) ||
    !nonnegativeInteger(value.display_order) ||
    availableFrom === undefined ||
    dueAt === undefined ||
    timezoneName === undefined ||
    (value.due_status !== "none" &&
      value.due_status !== "upcoming" &&
      value.due_status !== "overdue" &&
      value.due_status !== "unavailable") ||
    !nonnegativeInteger(value.record_version) ||
    value.record_version < 1 ||
    archivedAt === undefined ||
    restoredAt === undefined ||
    typeof value.created_at !== "string" ||
    typeof value.updated_at !== "string" ||
    (value.occurrence !== null && occurrence === null)
  ) return null;
  return {
    id: value.id,
    campaignId: value.campaign_id,
    campaignRecordVersion: value.campaign_record_version,
    campaignStatus: value.campaign_status,
    questType: value.quest_type,
    definitionState: value.definition_state,
    title: value.title,
    description,
    category,
    categoryLabel: value.category_label,
    rewardXp: value.reward_xp,
    displayOrder: value.display_order,
    availableFrom,
    dueAt,
    timezoneName,
    dueStatus: value.due_status,
    recordVersion: value.record_version,
    archivedAt,
    restoredAt,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
    occurrence,
  };
}

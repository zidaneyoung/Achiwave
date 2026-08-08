import type {
  Campaign,
  CampaignDetail,
  CampaignQuest,
  CampaignListItem,
  CampaignListPage,
  CampaignStatus,
  QuestDisplayStatus,
} from "./types";
import type { QuestCategory, QuestDifficulty } from "../quests/types";

export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return typeof value === "string" ? value : undefined;
}

function isQuestCategory(value: unknown): value is QuestCategory {
  return (
    value === "personal" ||
    value === "health" ||
    value === "learning" ||
    value === "work" ||
    value === "finance"
  );
}

function isQuestDifficulty(value: unknown): value is QuestDifficulty {
  return value === "easy" || value === "medium" || value === "hard";
}

function isCampaignStatus(value: unknown): value is CampaignStatus {
  return value === "active" || value === "completed" || value === "archived";
}

export function parseCampaign(value: unknown): Campaign | null {
  if (!isObject(value)) return null;
  const description = nullableString(value.description);
  const completedAt = nullableString(value.completed_at);
  const archivedAt = nullableString(value.archived_at);
  const restoredAt = nullableString(value.restored_at);
  if (
    typeof value.id !== "string" ||
    typeof value.title !== "string" ||
    description === undefined ||
    typeof value.display_order !== "number" ||
    !isCampaignStatus(value.status) ||
    typeof value.record_version !== "number" ||
    completedAt === undefined ||
    archivedAt === undefined ||
    restoredAt === undefined ||
    typeof value.created_at !== "string" ||
    typeof value.updated_at !== "string"
  ) {
    return null;
  }
  return {
    id: value.id,
    title: value.title,
    description,
    displayOrder: value.display_order,
    status: value.status,
    recordVersion: value.record_version,
    completedAt,
    archivedAt,
    restoredAt,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
  };
}

function parseNonnegativeInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value >= 0
    ? value
    : null;
}

export function parseCampaignListItem(value: unknown): CampaignListItem | null {
  const campaign = parseCampaign(value);
  if (!campaign || !isObject(value) || !isObject(value.quest_summary)) return null;
  const active = parseNonnegativeInteger(value.quest_summary.active);
  const archived = parseNonnegativeInteger(value.quest_summary.archived);
  const total = parseNonnegativeInteger(value.quest_summary.total);
  if (active === null || archived === null || total === null || total !== active + archived) {
    return null;
  }
  return { ...campaign, questSummary: { active, archived, total } };
}

export function parseCampaignList(value: unknown): CampaignListPage | null {
  if (!isObject(value) || !Array.isArray(value.items)) return null;
  const items = value.items.map(parseCampaignListItem);
  const total = parseNonnegativeInteger(value.total);
  const limit = parseNonnegativeInteger(value.limit);
  const offset = parseNonnegativeInteger(value.offset);
  if (
    items.some((item) => item === null) ||
    total === null ||
    limit === null ||
    limit < 1 ||
    offset === null
  ) {
    return null;
  }
  return {
    items: items as CampaignListItem[],
    total,
    limit,
    offset,
  };
}

function isQuestStatus(value: unknown): value is QuestDisplayStatus {
  return (
    value === "active" ||
    value === "archived" ||
    value === "scheduled" ||
    value === "available" ||
    value === "completed" ||
    value === "reversed" ||
    value === "expired" ||
    value === "voided"
  );
}

function parseCampaignQuest(value: unknown): CampaignQuest | null {
  if (!isObject(value)) return null;
  const description = nullableString(value.description);
  const category = value.category === null
    ? null
    : isQuestCategory(value.category)
      ? value.category
      : undefined;
  const difficulty = value.difficulty === null
    ? null
    : isQuestDifficulty(value.difficulty)
      ? value.difficulty
      : undefined;
  const availableFrom = nullableString(value.available_from);
  const dueAt = nullableString(value.due_at);
  const timezoneName = nullableString(value.timezone_name);
  const archivedAt = nullableString(value.archived_at);
  const restoredAt = nullableString(value.restored_at);
  if (
    typeof value.id !== "string" ||
    typeof value.campaign_id !== "string" ||
    (value.quest_type !== "one_time" && value.quest_type !== "recurring") ||
    (value.definition_state !== "active" && value.definition_state !== "archived") ||
    !isQuestStatus(value.status) ||
    typeof value.title !== "string" ||
    description === undefined ||
    category === undefined ||
    typeof value.category_label !== "string" ||
    value.category_label.length === 0 ||
    difficulty === undefined ||
    typeof value.difficulty_label !== "string" ||
    value.difficulty_label.length === 0 ||
    parseNonnegativeInteger(value.reward_xp) === null ||
    parseNonnegativeInteger(value.display_order) === null ||
    availableFrom === undefined ||
    dueAt === undefined ||
    timezoneName === undefined ||
    (value.due_status !== "none" &&
      value.due_status !== "upcoming" &&
      value.due_status !== "overdue" &&
      value.due_status !== "unavailable") ||
    parseNonnegativeInteger(value.record_version) === null ||
    archivedAt === undefined ||
    restoredAt === undefined ||
    typeof value.created_at !== "string" ||
    typeof value.updated_at !== "string"
  ) {
    return null;
  }
  return {
    id: value.id,
    campaignId: value.campaign_id,
    questType: value.quest_type,
    definitionState: value.definition_state,
    status: value.status,
    title: value.title,
    description,
    category,
    categoryLabel: value.category_label,
    difficulty,
    difficultyLabel: value.difficulty_label,
    rewardXp: value.reward_xp as number,
    displayOrder: value.display_order as number,
    availableFrom,
    dueAt,
    timezoneName,
    dueStatus: value.due_status,
    recordVersion: value.record_version as number,
    archivedAt,
    restoredAt,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
  };
}

export function parseCampaignDetail(value: unknown): CampaignDetail | null {
  const campaign = parseCampaign(value);
  if (!campaign || !isObject(value) || !isObject(value.quest_summary) || !Array.isArray(value.quests)) {
    return null;
  }
  const active = parseNonnegativeInteger(value.quest_summary.active);
  const archived = parseNonnegativeInteger(value.quest_summary.archived);
  const total = parseNonnegativeInteger(value.quest_summary.total);
  const quests = value.quests.map(parseCampaignQuest);
  if (
    active === null ||
    archived === null ||
    total === null ||
    total !== active + archived ||
    quests.some((quest) => quest === null)
  ) {
    return null;
  }
  return {
    ...campaign,
    questSummary: { active, archived, total },
    quests: quests as CampaignQuest[],
  };
}

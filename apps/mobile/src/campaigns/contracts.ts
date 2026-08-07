import type {
  Campaign,
  CampaignListItem,
  CampaignListPage,
  CampaignStatus,
} from "./types";

export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function nullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return typeof value === "string" ? value : undefined;
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

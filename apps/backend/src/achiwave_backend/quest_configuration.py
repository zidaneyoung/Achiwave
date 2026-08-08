from enum import StrEnum


class QuestCategory(StrEnum):
    PERSONAL = "personal"
    HEALTH = "health"
    LEARNING = "learning"
    WORK = "work"
    FINANCE = "finance"


QUEST_CATEGORY_LABELS: dict[QuestCategory, str] = {
    QuestCategory.PERSONAL: "Personal",
    QuestCategory.HEALTH: "Health",
    QuestCategory.LEARNING: "Learning",
    QuestCategory.WORK: "Work",
    QuestCategory.FINANCE: "Finance",
}


def quest_category_label(value: str | None) -> str:
    return "Uncategorized" if value is None else QUEST_CATEGORY_LABELS[QuestCategory(value)]

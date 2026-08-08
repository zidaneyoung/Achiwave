from enum import StrEnum


class QuestCategory(StrEnum):
    PERSONAL = "personal"
    HEALTH = "health"
    LEARNING = "learning"
    WORK = "work"
    FINANCE = "finance"


class QuestDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


QUEST_CATEGORY_LABELS: dict[QuestCategory, str] = {
    QuestCategory.PERSONAL: "Personal",
    QuestCategory.HEALTH: "Health",
    QuestCategory.LEARNING: "Learning",
    QuestCategory.WORK: "Work",
    QuestCategory.FINANCE: "Finance",
}

QUEST_DIFFICULTY_LABELS: dict[QuestDifficulty, str] = {
    QuestDifficulty.EASY: "Easy",
    QuestDifficulty.MEDIUM: "Medium",
    QuestDifficulty.HARD: "Hard",
}


def quest_category_label(value: str | None) -> str:
    return "Uncategorized" if value is None else QUEST_CATEGORY_LABELS[QuestCategory(value)]


def quest_difficulty_label(value: str | None) -> str:
    return "Not set" if value is None else QUEST_DIFFICULTY_LABELS[QuestDifficulty(value)]

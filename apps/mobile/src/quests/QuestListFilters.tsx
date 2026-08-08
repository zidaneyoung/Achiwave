import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";

import type { CampaignListItem } from "../campaigns/types";
import { AppButton } from "../components/AppButton";
import { AppTextField } from "../components/FormControls";
import { AppBottomSheet } from "../components/Overlays";
import { AppText } from "../theme/AppText";
import { spacing } from "../theme/tokens";
import {
  createEmptyQuestListFilters,
  QUEST_LIST_STATUS_OPTIONS,
  validateQuestListDates,
} from "./list";
import type {
  QuestAuthoringOption,
  QuestCategory,
  QuestListCategory,
  QuestListFilters,
  QuestListStatus,
} from "./types";

interface Choice<TValue extends string> {
  value: TValue | null;
  label: string;
}

function FilterChoiceGroup<TValue extends string>({
  label,
  onChange,
  options,
  selected,
  singleColumn = false,
}: {
  label: string;
  onChange: (value: TValue | null) => void;
  options: ReadonlyArray<Choice<TValue>>;
  selected: TValue | null;
  singleColumn?: boolean;
}) {
  return (
    <View style={styles.section}>
      <AppText accessibilityRole="header" variant="title">{label}</AppText>
      <View style={styles.choices}>
        {options.map((option) => {
          const isSelected = selected === option.value;
          return (
            <View
              key={option.value ?? "__all__"}
              style={singleColumn ? styles.fullChoice : styles.choice}
            >
              <AppButton
                accessibilityHint={isSelected ? "Current filter" : `Filter by ${option.label}`}
                accessibilityLabel={option.label}
                accessibilityState={{ selected: isSelected }}
                label={`${option.label}${isSelected ? " (selected)" : ""}`}
                onPress={() => onChange(option.value)}
                variant={isSelected ? "secondary" : "ghost"}
              />
            </View>
          );
        })}
      </View>
    </View>
  );
}

export function QuestListFiltersSheet({
  campaigns,
  categoryOptions,
  choicesError,
  choicesLoading,
  filters,
  onApply,
  onClear,
  onDismiss,
  onRetryChoices,
  visible,
}: {
  campaigns: CampaignListItem[];
  categoryOptions: QuestAuthoringOption<QuestCategory>[];
  choicesError: string | null;
  choicesLoading: boolean;
  filters: QuestListFilters;
  onApply: (filters: QuestListFilters) => void;
  onClear: () => void;
  onDismiss: () => void;
  onRetryChoices: () => void;
  visible: boolean;
}) {
  const [draft, setDraft] = useState<QuestListFilters>(filters);
  const [dateErrors, setDateErrors] = useState({ dueFrom: null as string | null, dueTo: null as string | null });

  useEffect(() => {
    if (visible) {
      setDraft({ ...filters });
      setDateErrors({ dueFrom: null, dueTo: null });
    }
  }, [filters, visible]);

  const campaignChoices: Array<Choice<string>> = [
    { value: null, label: "All current campaigns" },
    ...campaigns.map((campaign) => ({
      value: campaign.id,
      label: `${campaign.title}${campaign.status === "archived" ? " (archived)" : ""}`,
    })),
  ];
  const statusChoices: Array<Choice<QuestListStatus>> = [
    { value: null, label: "Current (not archived)" },
    ...QUEST_LIST_STATUS_OPTIONS,
  ];
  const categoryChoices: Array<Choice<QuestListCategory>> = [
    { value: null, label: "All categories" },
    { value: "uncategorized", label: "Uncategorized" },
    ...categoryOptions,
  ];

  function applyFilters() {
    const trimmed = {
      ...draft,
      dueFrom: draft.dueFrom.trim(),
      dueTo: draft.dueTo.trim(),
    };
    const errors = validateQuestListDates(trimmed);
    setDateErrors(errors);
    if (errors.dueFrom || errors.dueTo) return;
    onApply(trimmed);
  }

  return (
    <AppBottomSheet
      description="Choose any combination. Due dates are inclusive calendar dates in your saved account timezone."
      dismissLabel="Cancel"
      onDismiss={onDismiss}
      title="Filter quests"
      visible={visible}
    >
      <View style={styles.content}>
        {choicesLoading ? (
          <AppText accessibilityLiveRegion="polite" tone="muted">Loading campaign and category choices…</AppText>
        ) : null}
        {choicesError ? (
          <View accessibilityRole="alert" style={styles.choiceError}>
            <AppText tone="error">{choicesError}</AppText>
            <AppButton label="Retry choices" onPress={onRetryChoices} variant="secondary" />
          </View>
        ) : null}
        <FilterChoiceGroup
          label="Campaign"
          onChange={(campaignId) => setDraft((current) => ({ ...current, campaignId }))}
          options={campaignChoices}
          selected={draft.campaignId}
          singleColumn
        />
        <FilterChoiceGroup
          label="Status"
          onChange={(status) => setDraft((current) => ({ ...current, status }))}
          options={statusChoices}
          selected={draft.status}
        />
        <FilterChoiceGroup
          label="Category"
          onChange={(category) => setDraft((current) => ({ ...current, category }))}
          options={categoryChoices}
          selected={draft.category}
        />
        <View style={styles.section}>
          <AppText accessibilityRole="header" variant="title">Due date</AppText>
          <AppTextField
            autoCapitalize="none"
            autoCorrect={false}
            errorText={dateErrors.dueFrom ?? undefined}
            helperText="Optional inclusive start date, YYYY-MM-DD."
            label="Due from"
            onChangeText={(dueFrom) => {
              setDraft((current) => ({ ...current, dueFrom }));
              if (dateErrors.dueFrom) setDateErrors((current) => ({ ...current, dueFrom: null }));
            }}
            placeholder="YYYY-MM-DD"
            value={draft.dueFrom}
          />
          <AppTextField
            autoCapitalize="none"
            autoCorrect={false}
            errorText={dateErrors.dueTo ?? undefined}
            helperText="Optional inclusive end date, YYYY-MM-DD."
            label="Due to"
            onChangeText={(dueTo) => {
              setDraft((current) => ({ ...current, dueTo }));
              if (dateErrors.dueTo) setDateErrors((current) => ({ ...current, dueTo: null }));
            }}
            placeholder="YYYY-MM-DD"
            value={draft.dueTo}
          />
        </View>
        <View style={styles.actions}>
          <AppButton icon="filter-check-outline" label="Apply filters" onPress={applyFilters} />
          <AppButton
            icon="filter-remove-outline"
            label="Clear all filters"
            onPress={() => {
              setDraft(createEmptyQuestListFilters());
              setDateErrors({ dueFrom: null, dueTo: null });
              onClear();
            }}
            variant="secondary"
          />
        </View>
      </View>
    </AppBottomSheet>
  );
}

const styles = StyleSheet.create({
  content: { gap: spacing.lg },
  section: { gap: spacing.sm },
  choices: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  choice: { flexBasis: "47%", flexGrow: 1 },
  fullChoice: { width: "100%" },
  choiceError: { gap: spacing.sm },
  actions: { gap: spacing.sm },
});

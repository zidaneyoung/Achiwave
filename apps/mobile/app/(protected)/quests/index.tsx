import { useCallback, useEffect, useRef, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { campaignApi } from "../../../src/campaigns/api";
import type { CampaignListItem } from "../../../src/campaigns/types";
import { AppButton } from "../../../src/components/AppButton";
import { AppListItem } from "../../../src/components/ContentSurfaces";
import { EmptyState } from "../../../src/components/EmptyState";
import { ErrorState } from "../../../src/components/ErrorState";
import { LoadingSkeleton } from "../../../src/components/LoadingSkeleton";
import { StatusBadge, type StatusTone } from "../../../src/components/StatusBadge";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { preferenceApi } from "../../../src/preferences/api";
import { formatPreferenceDateTime } from "../../../src/preferences/formatDate";
import type { DateFormatPreference } from "../../../src/preferences/types";
import { questApi, QuestRequestError } from "../../../src/quests/api";
import {
  countQuestListFilters,
  createEmptyQuestListFilters,
  QUEST_LIST_PAGE_SIZE,
  QUEST_LIST_STATUS_OPTIONS,
} from "../../../src/quests/list";
import { QuestListFiltersSheet } from "../../../src/quests/QuestListFilters";
import type {
  QuestAuthoringOption,
  QuestCategory,
  QuestListFilters,
  QuestListItem,
  QuestListStatus,
} from "../../../src/quests/types";
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

function statusLabel(status: QuestListStatus): string {
  return QUEST_LIST_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
}

function statusTone(status: QuestListStatus): StatusTone {
  if (status === "completed") return "success";
  if (status === "available" || status === "active") return "info";
  if (status === "reversed" || status === "expired") return "warning";
  if (status === "voided") return "error";
  return "neutral";
}

function questDueCopy(
  quest: QuestListItem,
  dateFormat: DateFormatPreference,
): string | undefined {
  if (!quest.dueAt || !quest.timezoneName) return undefined;
  const due = formatPreferenceDateTime(
    new Date(quest.dueAt),
    dateFormat,
    quest.timezoneName,
  );
  if (quest.dueStatus === "overdue") return `Due ${due} · Overdue (server confirmed)`;
  if (quest.dueStatus === "unavailable") return `Due ${due} · Unavailable`;
  return `Due ${due}`;
}

function QuestListRow({
  dateFormat,
  onPress,
  quest,
}: {
  dateFormat: DateFormatPreference;
  onPress: () => void;
  quest: QuestListItem;
}) {
  return (
    <AppListItem
      leading={
        <StatusBadge
          compact
          label={statusLabel(quest.status)}
          tone={statusTone(quest.status)}
        />
      }
      metadata={`${quest.campaignTitle} · ${quest.categoryLabel} · ${quest.difficultyLabel} · ${quest.rewardXp} XP`}
      onPress={onPress}
      status={questDueCopy(quest, dateFormat)}
      title={quest.title}
    />
  );
}

function choiceErrorMessage(errors: unknown[]): string | null {
  if (errors.length === 0) return null;
  const reconnect = errors.some((error) => error instanceof Error && error.message.includes("Reconnect"));
  return reconnect
    ? "Reconnect to load all campaign and category choices. Status and date filters remain available."
    : "Some campaign or category choices are temporarily unavailable. Status and date filters remain available.";
}

async function loadAllCampaignChoices(
  view: "active" | "archived",
): Promise<CampaignListItem[]> {
  const items: CampaignListItem[] = [];
  while (true) {
    const page = await campaignApi.list(view, 100, items.length);
    items.push(...page.items);
    if (items.length >= page.total || page.items.length === 0) return items;
  }
}

export default function QuestListRoute() {
  const authentication = useAuthentication();
  const ownerId = authentication.state.status === "authenticated"
    ? authentication.state.user.id
    : null;
  if (!ownerId) return null;
  return <QuestListContent key={ownerId} ownerId={ownerId} />;
}

function QuestListContent({ ownerId }: { ownerId: string }) {
  const router = useRouter();
  const styles = useThemeStyles(createStyles);
  const [filters, setFilters] = useState<QuestListFilters>(createEmptyQuestListFilters);
  const [filterSheetVisible, setFilterSheetVisible] = useState(false);
  const [items, setItems] = useState<QuestListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [nextOffset, setNextOffset] = useState(0);
  const [listError, setListError] = useState<string | null>(null);
  const [nextPageError, setNextPageError] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [campaignChoices, setCampaignChoices] = useState<CampaignListItem[]>([]);
  const [categoryOptions, setCategoryOptions] = useState<QuestAuthoringOption<QuestCategory>[]>([]);
  const [choicesLoading, setChoicesLoading] = useState(true);
  const [choicesError, setChoicesError] = useState<string | null>(null);
  const [dateFormat, setDateFormat] = useState<DateFormatPreference>("system");
  const listRequestSequence = useRef(0);
  const choiceRequestSequence = useRef(0);

  const loadFirstPage = useCallback(async () => {
    if (!ownerId) return;
    const request = ++listRequestSequence.current;
    setLoadingMore(false);
    setListError(null);
    setNextPageError(null);
    try {
      const page = await questApi.list(filters, QUEST_LIST_PAGE_SIZE, 0);
      if (request !== listRequestSequence.current) return;
      setItems(page.items);
      setTotal(page.total);
      setNextOffset(page.items.length);
    } catch (caught) {
      if (request !== listRequestSequence.current) return;
      setListError(
        caught instanceof QuestRequestError
          ? caught.message
          : "Quests could not be loaded.",
      );
    }
  }, [filters, ownerId]);

  const loadNextPage = useCallback(async () => {
    if (!ownerId || !items || loadingMore || nextOffset >= total) return;
    const request = ++listRequestSequence.current;
    const offset = nextOffset;
    setLoadingMore(true);
    setNextPageError(null);
    try {
      const page = await questApi.list(filters, QUEST_LIST_PAGE_SIZE, offset);
      if (request !== listRequestSequence.current) return;
      setItems((current) => {
        if (!current) return current;
        const knownIds = new Set(current.map((quest) => quest.id));
        return [...current, ...page.items.filter((quest) => !knownIds.has(quest.id))];
      });
      setTotal(page.total);
      setNextOffset(
        page.items.length === 0
          ? page.total
          : page.offset + page.items.length,
      );
    } catch (caught) {
      if (request !== listRequestSequence.current) return;
      setNextPageError(
        caught instanceof QuestRequestError
          ? caught.message
          : "More quests could not be loaded.",
      );
    } finally {
      if (request === listRequestSequence.current) setLoadingMore(false);
    }
  }, [filters, items, loadingMore, nextOffset, ownerId, total]);

  const loadChoices = useCallback(async () => {
    if (!ownerId) return;
    const request = ++choiceRequestSequence.current;
    setChoicesLoading(true);
    setChoicesError(null);
    const [activeCampaigns, archivedCampaigns, options] = await Promise.allSettled([
      loadAllCampaignChoices("active"),
      loadAllCampaignChoices("archived"),
      questApi.getAuthoringOptions(),
    ]);
    if (request !== choiceRequestSequence.current) return;
    const errors: unknown[] = [];
    const campaignMap = new Map<string, CampaignListItem>();
    for (const result of [activeCampaigns, archivedCampaigns]) {
      if (result.status === "fulfilled") {
        for (const campaign of result.value) campaignMap.set(campaign.id, campaign);
      } else {
        errors.push(result.reason);
      }
    }
    setCampaignChoices([...campaignMap.values()]);
    if (options.status === "fulfilled") {
      setCategoryOptions(options.value.categories);
    } else {
      errors.push(options.reason);
    }
    setChoicesError(choiceErrorMessage(errors));
    setChoicesLoading(false);
  }, [ownerId]);

  useFocusEffect(
    useCallback(() => {
      void loadFirstPage();
      return () => {
        listRequestSequence.current += 1;
      };
    }, [loadFirstPage]),
  );

  useEffect(() => {
    let mounted = true;
    void loadChoices();
    void preferenceApi.getAvailable().then((preferences) => {
      if (mounted) setDateFormat(preferences?.dateFormat ?? "system");
    });
    return () => {
      mounted = false;
      choiceRequestSequence.current += 1;
    };
  }, [loadChoices]);

  const activeFilterCount = countQuestListFilters(filters);
  const selectedCampaign = campaignChoices.find((campaign) => campaign.id === filters.campaignId);
  const selectedCategory = categoryOptions.find((option) => option.value === filters.category);
  const filterSummary = [
    selectedCampaign?.title,
    filters.status ? statusLabel(filters.status) : null,
    filters.category === "uncategorized" ? "Uncategorized" : selectedCategory?.label,
    filters.dueFrom ? `Due from ${filters.dueFrom}` : null,
    filters.dueTo ? `Due to ${filters.dueTo}` : null,
  ].filter((value): value is string => Boolean(value)).join(" · ");

  function applyFilters(nextFilters: QuestListFilters) {
    listRequestSequence.current += 1;
    setItems(null);
    setTotal(0);
    setNextOffset(0);
    setListError(null);
    setNextPageError(null);
    setFilters(nextFilters);
    setFilterSheetVisible(false);
  }

  function clearFilters() {
    applyFilters(createEmptyQuestListFilters());
  }

  const header = (
    <View style={styles.header}>
      <AppText tone="accent" variant="label">Quest planning</AppText>
      <AppText accessibilityRole="header" variant="display">Quests</AppText>
      <AppText tone="muted">
        Browse server-confirmed quest details across your campaigns.
      </AppText>
      <View style={styles.filterActions}>
        <AppButton
          accessibilityHint="Opens campaign, status, category, and due-date filters."
          icon="filter-variant"
          label={activeFilterCount === 0 ? "Filter quests" : `Filters (${activeFilterCount} active)`}
          onPress={() => setFilterSheetVisible(true)}
          variant={activeFilterCount === 0 ? "secondary" : "primary"}
        />
        {activeFilterCount > 0 ? (
          <AppButton
            icon="filter-remove-outline"
            label="Clear filters"
            onPress={clearFilters}
            variant="ghost"
          />
        ) : null}
      </View>
      {activeFilterCount > 0 ? (
        <AppText tone="muted" variant="caption">Showing: {filterSummary}</AppText>
      ) : null}
      {items !== null ? (
        <AppText accessibilityLiveRegion="polite" tone="subtle" variant="caption">
          {total === 1 ? "1 quest" : `${total} quests`}
        </AppText>
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <FlatList
        contentContainerStyle={[
          styles.list,
          items !== null && items.length === 0 && styles.emptyList,
        ]}
        data={items ?? []}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={header}
        ListEmptyComponent={
          items === null ? (
            listError ? (
              <View style={styles.state}>
                <ErrorState
                  kind={listError.includes("Reconnect") ? "network" : "fullScreen"}
                  onRetry={() => void loadFirstPage()}
                />
                <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>
                  {listError}
                </AppText>
              </View>
            ) : (
              <View style={styles.loading}>
                <LoadingSkeleton label="Loading quests" layout="list" />
                <LoadingSkeleton label="Loading quests" layout="list" />
                <LoadingSkeleton label="Loading quests" layout="list" />
              </View>
            )
          ) : (
            <EmptyState
              actionLabel={activeFilterCount > 0 ? "Clear filters" : "View campaigns"}
              description={
                activeFilterCount > 0
                  ? "Change or clear the current filters to see more quests."
                  : "Create a quest from a campaign, or use filters to browse archived history."
              }
              kind={activeFilterCount > 0 ? "filtered" : "firstUse"}
              onAction={
                activeFilterCount > 0
                  ? clearFilters
                  : () => router.replace(PROTECTED_ROUTES.campaigns)
              }
              title={activeFilterCount > 0 ? "No matching quests" : "No current quests"}
            />
          )
        }
        ListFooterComponent={
          items && items.length > 0 ? (
            <View style={styles.footer}>
              {listError ? (
                <View style={styles.sectionError}>
                  <ErrorState kind="section" onRetry={() => void loadFirstPage()} />
                  <AppText accessibilityLiveRegion="assertive" tone="error">{listError}</AppText>
                </View>
              ) : null}
              {nextPageError ? (
                <View style={styles.sectionError}>
                  <AppText accessibilityLiveRegion="assertive" tone="error">{nextPageError}</AppText>
                </View>
              ) : null}
              {nextOffset < total ? (
                <AppButton
                  label="Load more quests"
                  loading={loadingMore}
                  onPress={() => void loadNextPage()}
                  variant="secondary"
                />
              ) : null}
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <QuestListRow
            dateFormat={dateFormat}
            onPress={() => router.push(PROTECTED_ROUTES.questDetail(item.id))}
            quest={item}
          />
        )}
      />
      <QuestListFiltersSheet
        campaigns={campaignChoices}
        categoryOptions={categoryOptions}
        choicesError={choicesError}
        choicesLoading={choicesLoading}
        filters={filters}
        onApply={applyFilters}
        onClear={clearFilters}
        onDismiss={() => setFilterSheetVisible(false)}
        onRetryChoices={() => void loadChoices()}
        visible={filterSheetVisible}
      />
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  list: { gap: spacing.sm, padding: spacing.lg, paddingTop: spacing.sm },
  emptyList: { flexGrow: 1 },
  header: { gap: spacing.sm, paddingBottom: spacing.sm },
  filterActions: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  loading: { gap: spacing.md, paddingTop: spacing.sm },
  state: { flex: 1, justifyContent: "center", paddingVertical: spacing.xl },
  footer: { gap: spacing.sm, paddingTop: spacing.sm },
  sectionError: { gap: spacing.xs },
  center: { textAlign: "center" },
});

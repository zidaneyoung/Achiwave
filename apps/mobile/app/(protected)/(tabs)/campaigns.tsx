import { useCallback, useRef, useState } from "react";
import { AccessibilityInfo, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
import { useReducedMotion } from "../../../src/accessibility/ReducedMotionProvider";
import { campaignApi, CampaignRequestError } from "../../../src/campaigns/api";
import {
  getCachedCampaigns,
  setCachedCampaigns,
} from "../../../src/campaigns/cache";
import type {
  CampaignListItem,
  CampaignListView,
} from "../../../src/campaigns/types";
import { AppButton } from "../../../src/components/AppButton";
import { AppListItem } from "../../../src/components/ContentSurfaces";
import { EmptyState } from "../../../src/components/EmptyState";
import { ErrorState } from "../../../src/components/ErrorState";
import { LoadingSkeleton } from "../../../src/components/LoadingSkeleton";
import { StatusBadge } from "../../../src/components/StatusBadge";
import { PROTECTED_ROUTES } from "../../../src/navigation/routes";
import { createKeyedSingleFlight } from "../../../src/refresh/singleFlight";
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

function CampaignListRow({
  campaign,
  onPress,
}: {
  campaign: CampaignListItem;
  onPress: () => void;
}) {
  const questCopy =
    campaign.questSummary.total === 0
      ? "No quests"
      : `${campaign.questSummary.active} active, ${campaign.questSummary.archived} archived quests`;
  return (
    <AppListItem
      onPress={onPress}
      leading={
        <StatusBadge
          compact
          label={campaign.status === "completed" ? "Completed" : campaign.status === "archived" ? "Archived" : "Active"}
          tone={campaign.status === "completed" ? "success" : campaign.status === "archived" ? "neutral" : "info"}
        />
      }
      metadata={questCopy}
      status={`Updated ${new Date(campaign.updatedAt).toLocaleDateString()}`}
      title={campaign.title}
    />
  );
}

export default function CampaignsTabRoute() {
  const router = useRouter();
  const authentication = useAuthentication();
  const reduceMotion = useReducedMotion();
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const ownerId =
    authentication.state.status === "authenticated"
      ? authentication.state.user.id
      : null;
  const [view, setView] = useState<CampaignListView>("active");
  const [items, setItems] = useState<CampaignListItem[] | null>(() =>
    ownerId ? getCachedCampaigns(ownerId, "active") : null,
  );
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const requestSequence = useRef(0);
  const contentRef = useRef(items);
  const manualRefreshRef = useRef(false);
  const manualRefreshGeneration = useRef(0);
  const [requests] = useState(() => createKeyedSingleFlight<Awaited<ReturnType<typeof campaignApi.list>>>());
  contentRef.current = items;

  const load = useCallback(async (reason: "focus" | "manual" | "retry" = "focus") => {
    if (!ownerId) return;
    let manualGeneration: number | null = null;
    if (reason === "manual") {
      if (manualRefreshRef.current) return;
      manualRefreshRef.current = true;
      manualGeneration = ++manualRefreshGeneration.current;
      setRefreshing(true);
    }
    const request = ++requestSequence.current;
    const cached = getCachedCampaigns(ownerId, view);
    if (contentRef.current === null && cached !== null) {
      contentRef.current = cached;
      setItems(cached);
    }
    const hadContent = contentRef.current !== null;
    if (hadContent) setRefreshError(null);
    else setError(null);
    try {
      const { promise } = requests.run(
        `${ownerId}:${view}`,
        () => campaignApi.list(view),
      );
      const page = await promise;
      if (request !== requestSequence.current) return;
      setCachedCampaigns(ownerId, view, page.items);
      contentRef.current = page.items;
      setItems(page.items);
      setError(null);
      setRefreshError(null);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility("Campaigns refreshed.");
      }
    } catch (caught) {
      if (request !== requestSequence.current) return;
      const message = caught instanceof CampaignRequestError
        ? caught.message
        : "Campaigns could not be loaded.";
      if (hadContent) setRefreshError(message);
      else setError(message);
      if (reason === "manual") {
        AccessibilityInfo.announceForAccessibility(`Campaign refresh failed. ${message}`);
      }
    } finally {
      if (reason === "manual" && manualGeneration === manualRefreshGeneration.current) {
        manualRefreshRef.current = false;
        setRefreshing(false);
      }
    }
  }, [ownerId, requests, view]);

  useFocusEffect(
    useCallback(() => {
      void load("focus");
      return () => {
        requestSequence.current += 1;
        manualRefreshGeneration.current += 1;
        manualRefreshRef.current = false;
        setRefreshing(false);
      };
    }, [load]),
  );

  const selectView = useCallback((nextView: CampaignListView) => {
    requestSequence.current += 1;
    manualRefreshGeneration.current += 1;
    manualRefreshRef.current = false;
    setRefreshing(false);
    setView(nextView);
    const cached = ownerId ? getCachedCampaigns(ownerId, nextView) : null;
    contentRef.current = cached;
    setItems(cached);
    setError(null);
    setRefreshError(null);
  }, [ownerId]);

  if (!ownerId) return null;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <AppText tone="accent" variant="label">Objectives</AppText>
        <AppText accessibilityRole="header" variant="display">Campaigns</AppText>
        <AppText tone="muted">
          Server-confirmed objectives and lifecycle state.
        </AppText>
        <View accessibilityRole="tablist" style={styles.tabs}>
          <AppButton
            accessibilityRole="tab"
            accessibilityState={{ selected: view === "active" }}
            label="Active"
            onPress={() => selectView("active")}
            variant={view === "active" ? "primary" : "secondary"}
          />
          <AppButton
            accessibilityRole="tab"
            accessibilityState={{ selected: view === "archived" }}
            label="Archived"
            onPress={() => selectView("archived")}
            variant={view === "archived" ? "primary" : "secondary"}
          />
        </View>
        <AppButton
          icon="format-list-checks"
          label="Browse all quests"
          onPress={() => router.push(PROTECTED_ROUTES.questList)}
          variant="secondary"
        />
        {view === "active" ? (
          <AppButton
            icon="plus"
            label="Create campaign"
            onPress={() => router.push(PROTECTED_ROUTES.campaignCreate)}
          />
        ) : null}
      </View>
      {items === null && !error ? (
        <View style={styles.loading}>
          <LoadingSkeleton label="Loading campaigns" layout="list" />
          <LoadingSkeleton label="Loading campaigns" layout="list" />
          <LoadingSkeleton label="Loading campaigns" layout="list" />
        </View>
      ) : null}
      {items === null && error ? (
        <View style={styles.state}>
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load("retry")} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {items !== null ? (
        <FlatList
          contentContainerStyle={[styles.list, items.length === 0 && styles.emptyList]}
          data={items}
          keyExtractor={(item) => item.id}
          refreshControl={
            <RefreshControl
              colors={[theme.colors.accent]}
              enabled={!refreshing}
              onRefresh={() => void load("manual")}
              progressBackgroundColor={theme.colors.surface}
              refreshing={refreshing && !reduceMotion}
              tintColor={theme.colors.accent}
            />
          }
          ListEmptyComponent={
            <EmptyState
              actionLabel={view === "active" ? "Create campaign" : undefined}
              description={
                view === "active"
                  ? "Create your first objective, then add quests when ready."
                  : "Archived campaigns will appear here without losing history."
              }
              kind="firstUse"
              onAction={view === "active" ? () => router.push(PROTECTED_ROUTES.campaignCreate) : undefined}
              title={view === "active" ? "No campaigns yet" : "No archived campaigns"}
            />
          }
          ListFooterComponent={
            refreshError ? (
              <View style={styles.sectionError}>
                <ErrorState kind="section" onRetry={() => void load("retry")} />
                <AppText accessibilityLiveRegion="assertive" tone="error">
                  Campaign refresh failed. {refreshError}
                </AppText>
              </View>
            ) : refreshing && reduceMotion ? (
              <AppText accessibilityLiveRegion="polite" tone="muted" style={styles.center}>
                Refreshing campaigns…
              </AppText>
            ) : null
          }
          renderItem={({ item }) => (
            <CampaignListRow
              campaign={item}
              onPress={() => router.push(PROTECTED_ROUTES.campaignDetail(item.id))}
            />
          )}
        />
      ) : null}
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  header: { gap: spacing.sm, padding: spacing.lg, paddingBottom: spacing.sm },
  tabs: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  loading: { gap: spacing.md, padding: spacing.lg },
  list: { gap: spacing.sm, padding: spacing.lg, paddingTop: spacing.sm },
  emptyList: { flexGrow: 1, justifyContent: "center" },
  state: { flex: 1, justifyContent: "center", padding: spacing.lg },
  sectionError: { gap: spacing.xs, marginTop: spacing.md },
  center: { textAlign: "center" },
});

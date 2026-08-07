import { useCallback, useRef, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../../src/auth/AuthContext";
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
import { AppText } from "../../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../../src/theme/ThemeProvider";
import { spacing } from "../../../src/theme/tokens";

function CampaignListRow({ campaign }: { campaign: CampaignListItem }) {
  const questCopy =
    campaign.questSummary.total === 0
      ? "No quests"
      : `${campaign.questSummary.active} active, ${campaign.questSummary.archived} archived quests`;
  return (
    <AppListItem
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
  const requestSequence = useRef(0);

  const load = useCallback(async () => {
    if (!ownerId) return;
    const request = ++requestSequence.current;
    const cached = getCachedCampaigns(ownerId, view);
    setItems(cached);
    setRefreshing(cached !== null);
    setError(null);
    try {
      const page = await campaignApi.list(view);
      if (request !== requestSequence.current) return;
      setCachedCampaigns(ownerId, view, page.items);
      setItems(page.items);
    } catch (caught) {
      if (request !== requestSequence.current) return;
      setError(
        caught instanceof CampaignRequestError
          ? caught.message
          : "Campaigns could not be loaded.",
      );
    } finally {
      if (request === requestSequence.current) setRefreshing(false);
    }
  }, [ownerId, view]);

  useFocusEffect(
    useCallback(() => {
      void load();
      return () => {
        requestSequence.current += 1;
      };
    }, [load]),
  );

  const selectView = useCallback((nextView: CampaignListView) => {
    setView(nextView);
    setItems(null);
    setError(null);
  }, []);

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
          <ErrorState kind={error.includes("Reconnect") ? "network" : "fullScreen"} onRetry={() => void load()} />
          <AppText accessibilityLiveRegion="assertive" tone="error" style={styles.center}>{error}</AppText>
        </View>
      ) : null}
      {items !== null ? (
        <FlatList
          contentContainerStyle={[styles.list, items.length === 0 && styles.emptyList]}
          data={items}
          keyExtractor={(item) => item.id}
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
            error ? (
              <View style={styles.sectionError}>
                <ErrorState kind="section" onRetry={() => void load()} />
                <AppText accessibilityLiveRegion="assertive" tone="error">{error}</AppText>
              </View>
            ) : refreshing ? (
              <AppText accessibilityLiveRegion="polite" tone="muted" style={styles.center}>
                Refreshing campaigns…
              </AppText>
            ) : null
          }
          renderItem={({ item }) => <CampaignListRow campaign={item} />}
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

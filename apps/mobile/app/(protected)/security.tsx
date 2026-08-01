import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  deviceManagementApi,
  type DeviceSnapshot,
  type SessionSnapshot,
} from "../../src/devices/api";
import {
  type AchiwaveTheme,
  useAchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";
import { borders, radii, sizing, spacing, typography } from "../../src/theme/tokens";

function displayTimestamp(value: string | null): string {
  if (!value) {
    return "Not recorded";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "Not recorded" : parsed.toLocaleString();
}

export default function DeviceSecurityRoute() {
  const theme = useAchiwaveTheme();
  const styles = useThemeStyles(createStyles);
  const [devices, setDevices] = useState<DeviceSnapshot[]>([]);
  const [sessions, setSessions] = useState<SessionSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [workingId, setWorkingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      const [nextDevices, nextSessions] = await Promise.all([
        deviceManagementApi.listDevices(),
        deviceManagementApi.listSessions(),
      ]);
      setDevices(nextDevices);
      setSessions(nextSessions);
    } catch {
      setMessage("Devices and sessions could not be loaded. Check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function revokeDevice(device: DeviceSnapshot): Promise<void> {
    setWorkingId(device.id);
    setMessage(null);
    try {
      await deviceManagementApi.revokeDevice(device.id);
      if (!device.isCurrent) {
        setMessage("Device access was revoked.");
        await load();
      }
    } catch {
      setMessage("Device access could not be revoked. Try again.");
    } finally {
      setWorkingId(null);
    }
  }

  async function revokeSession(session: SessionSnapshot): Promise<void> {
    setWorkingId(session.id);
    setMessage(null);
    try {
      await deviceManagementApi.revokeSession(session.id);
      if (!session.isCurrent) {
        setMessage("Session access was revoked.");
        await load();
      }
    } catch {
      setMessage("Session access could not be revoked. Try again.");
    } finally {
      setWorkingId(null);
    }
  }

  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Devices and sessions
        </Text>
        <Text style={styles.introduction}>
          Review access to your account. Revoking this device signs you out.
        </Text>
        {message ? (
          <Text accessibilityLiveRegion="polite" style={styles.message}>
            {message}
          </Text>
        ) : null}
        {loading ? (
          <ActivityIndicator
            accessibilityLabel="Loading devices and sessions"
            color={theme.colors.accent}
            size="large"
            style={styles.loading}
          />
        ) : (
          <>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Devices
            </Text>
            {devices.map((device) => (
              <View key={device.id} style={styles.card}>
                <Text style={styles.cardTitle}>
                  {device.label}{device.isCurrent ? " (this device)" : ""}
                </Text>
                <Text style={styles.detail}>State: {device.state}</Text>
                <Text style={styles.detail}>
                  Last seen: {displayTimestamp(device.lastSeenAt)}
                </Text>
                {device.state === "active" ? (
                  <Pressable
                    accessibilityRole="button"
                    disabled={workingId !== null}
                    onPress={() => void revokeDevice(device)}
                    style={({ pressed }) => [
                      styles.revokeButton,
                      pressed && styles.revokeButtonPressed,
                      workingId !== null && styles.disabled,
                    ]}
                  >
                    <Text style={styles.revokeButtonText}>
                      {workingId === device.id ? "Revoking..." : "Revoke device"}
                    </Text>
                  </Pressable>
                ) : null}
              </View>
            ))}

            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Sessions
            </Text>
            {sessions.map((session) => (
              <View key={session.id} style={styles.card}>
                <Text style={styles.cardTitle}>
                  {session.deviceLabel}{session.isCurrent ? " (current session)" : ""}
                </Text>
                <Text style={styles.detail}>State: {session.state}</Text>
                <Text style={styles.detail}>
                  Started: {displayTimestamp(session.createdAt)}
                </Text>
                {session.state === "active" ? (
                  <Pressable
                    accessibilityRole="button"
                    disabled={workingId !== null}
                    onPress={() => void revokeSession(session)}
                    style={({ pressed }) => [
                      styles.revokeButton,
                      pressed && styles.revokeButtonPressed,
                      workingId !== null && styles.disabled,
                    ]}
                  >
                    <Text style={styles.revokeButtonText}>
                      {workingId === session.id ? "Revoking..." : "Revoke session"}
                    </Text>
                  </Pressable>
                ) : null}
              </View>
            ))}
          </>
        )}
        {!loading && message ? (
          <Pressable
            accessibilityRole="button"
            onPress={() => void load()}
            style={styles.retryButton}
          >
            <Text style={styles.retryButtonText}>Refresh</Text>
          </Pressable>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  container: { padding: spacing.lg, paddingBottom: spacing.xxxl },
  title: { color: theme.colors.foreground, ...typography.heading1 },
  introduction: { color: theme.colors.foregroundMuted, ...typography.body, marginTop: spacing.sm },
  message: { color: theme.colors.warning, ...typography.body, marginTop: spacing.md },
  loading: { marginTop: spacing.xl },
  sectionTitle: { color: theme.colors.foreground, ...typography.heading2, marginTop: spacing.xl },
  card: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.md,
    borderWidth: borders.thin,
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  cardTitle: { color: theme.colors.foreground, ...typography.title },
  detail: { color: theme.colors.foregroundSubtle, ...typography.body, marginTop: spacing.xs },
  revokeButton: {
    alignItems: "center",
    borderColor: theme.colors.error,
    borderRadius: radii.md,
    borderWidth: borders.selected,
    justifyContent: "center",
    marginTop: spacing.md,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  revokeButtonPressed: { backgroundColor: theme.colors.errorSurface },
  revokeButtonText: { color: theme.colors.error, ...typography.label },
  disabled: { opacity: 0.6 },
  retryButton: {
    alignItems: "center",
    backgroundColor: theme.colors.action,
    borderRadius: radii.md,
    justifyContent: "center",
    marginTop: spacing.md,
    minHeight: sizing.minimumTouchTarget,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  retryButtonText: { color: theme.colors.onAction, ...typography.label },
});

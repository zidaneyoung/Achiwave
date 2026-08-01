import type { ReactNode } from "react";
import {
  Modal,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AppButton } from "./AppButton";
import { AppText } from "../theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { borders, radii, sizing, spacing } from "../theme/tokens";

interface OverlayProps {
  visible: boolean;
  title: string;
  description?: string;
  children?: ReactNode;
  onDismiss: () => void;
}

export interface AppDialogProps extends OverlayProps {
  kind?: "information" | "confirmation" | "destructive";
  confirmLabel?: string;
  onConfirm?: () => void;
}

export function AppDialog({
  children,
  confirmLabel = "Confirm",
  description,
  kind = "information",
  onConfirm,
  onDismiss,
  title,
  visible,
}: AppDialogProps) {
  const styles = useThemeStyles(createStyles);
  return (
    <Modal
      animationType="fade"
      onRequestClose={onDismiss}
      statusBarTranslucent
      transparent
      visible={visible}
    >
      <SafeAreaView style={styles.overlay}>
        <View accessibilityViewIsModal style={styles.dialog}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <AppText accessibilityRole="header" variant="heading2">{title}</AppText>
            {description ? <AppText tone="muted" style={styles.description}>{description}</AppText> : null}
            {children ? <View style={styles.body}>{children}</View> : null}
          </ScrollView>
          <View style={styles.actions}>
            {kind !== "information" && onConfirm ? (
              <AppButton
                label={confirmLabel}
                onPress={onConfirm}
                variant={kind === "destructive" ? "destructive" : "primary"}
              />
            ) : null}
            <AppButton label={kind === "information" ? "Close" : "Cancel"} onPress={onDismiss} variant="secondary" />
          </View>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

export interface AppBottomSheetProps extends OverlayProps {
  dismissLabel?: string;
}

export function AppBottomSheet({
  children,
  description,
  dismissLabel = "Done",
  onDismiss,
  title,
  visible,
}: AppBottomSheetProps) {
  const styles = useThemeStyles(createStyles);
  return (
    <Modal
      animationType="slide"
      onRequestClose={onDismiss}
      statusBarTranslucent
      transparent
      visible={visible}
    >
      <SafeAreaView style={[styles.overlay, styles.sheetOverlay]}>
        <View accessibilityViewIsModal style={styles.sheet}>
          <View accessibilityElementsHidden style={styles.handle} />
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <AppText accessibilityRole="header" variant="heading2">{title}</AppText>
            {description ? <AppText tone="muted" style={styles.description}>{description}</AppText> : null}
            {children ? <View style={styles.body}>{children}</View> : null}
          </ScrollView>
          <View style={styles.actions}>
            <AppButton label={dismissLabel} onPress={onDismiss} />
          </View>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  overlay: {
    alignItems: "center",
    backgroundColor: theme.colors.overlay,
    flex: 1,
    justifyContent: "center",
    padding: spacing.lg,
  },
  dialog: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderRadius: radii.lg,
    borderWidth: borders.thin,
    maxHeight: "85%",
    maxWidth: sizing.contentMeasure,
    overflow: "hidden",
    width: "100%",
  },
  sheetOverlay: { justifyContent: "flex-end", padding: 0 },
  sheet: {
    backgroundColor: theme.colors.surface,
    borderColor: theme.colors.border,
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    borderTopWidth: borders.thin,
    maxHeight: "88%",
    overflow: "hidden",
    width: "100%",
  },
  handle: {
    alignSelf: "center",
    backgroundColor: theme.colors.borderStrong,
    borderRadius: radii.pill,
    height: spacing.xxs,
    marginTop: spacing.sm,
    width: spacing.xxl,
  },
  scrollContent: { padding: spacing.lg },
  description: { marginTop: spacing.sm },
  body: { marginTop: spacing.md },
  actions: { gap: spacing.sm, padding: spacing.lg, paddingTop: 0 },
});

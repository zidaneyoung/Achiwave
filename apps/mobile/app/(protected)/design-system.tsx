import { useState } from "react";
import { Redirect } from "expo-router";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AppButton } from "../../src/components/AppButton";
import { AppSelector, AppTextField } from "../../src/components/FormControls";
import { AppCard, AppListItem } from "../../src/components/ContentSurfaces";
import { AppBottomSheet, AppDialog } from "../../src/components/Overlays";
import { ProgressIndicator } from "../../src/components/ProgressIndicator";
import { PROTECTED_ROUTES } from "../../src/navigation/routes";
import { AppText } from "../../src/theme/AppText";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";
import { spacing } from "../../src/theme/tokens";

export default function DesignSystemRoute() {
  const styles = useThemeStyles(createStyles);
  const [fieldValue, setFieldValue] = useState("");
  const [selectorExpanded, setSelectorExpanded] = useState(false);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [sheetVisible, setSheetVisible] = useState(false);
  if (!__DEV__) {
    return <Redirect href={PROTECTED_ROUTES.home} />;
  }
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <AppText accessibilityRole="header" variant="display">Component showcase</AppText>
        <AppText tone="muted" style={styles.introduction}>
          Development-only examples for themes, variants, long labels, and states.
        </AppText>
        <ShowcaseSection title="Buttons">
          <AppButton label="Continue" />
          <AppButton label="Review details" variant="secondary" />
          <AppButton label="A deliberately long action label that wraps safely" variant="ghost" />
          <AppButton label="Delete example" variant="destructive" />
          <AppButton icon="tune-variant" iconOnly label="Adjust showcase" variant="secondary" />
          <AppButton disabled label="Unavailable action" />
          <AppButton label="Saving" loading />
        </ShowcaseSection>
        <ShowcaseSection title="Inputs and selectors">
          <AppTextField
            helperText="Helper text remains associated with the field."
            label="Display name"
            onChangeText={setFieldValue}
            placeholder="Enter a name"
            value={fieldValue}
          />
          <AppTextField
            errorText="Use at least 12 characters."
            label="Password"
            required
            secureTextEntry
            value="short"
          />
          <AppTextField editable={false} label="Disabled field" value="Unavailable" />
          <AppSelector
            expanded={selectorExpanded}
            helperText="Current selection is announced."
            label="Theme example"
            onPress={() => setSelectorExpanded((value) => !value)}
            value="Follow system"
          />
        </ShowcaseSection>
        <ShowcaseSection title="Cards and list items">
          <AppCard metadata="Static surface" status="Example status" title="Daily focus">
            <AppText tone="muted">Compact content keeps its hierarchy at narrow widths.</AppText>
          </AppCard>
          <AppCard accessibilityHint="Opens this example card." metadata="Interactive" onPress={() => undefined} title="Review progress" />
          <AppListItem metadata="No nested action" onPress={() => undefined} title="Interactive list item" />
          <AppListItem
            metadata="Trailing action stops parent activation"
            onPress={() => undefined}
            onTrailingActionPress={() => undefined}
            title="List item with action"
            trailingActionLabel="More options for list item"
          />
        </ShowcaseSection>
        <ShowcaseSection title="Dialogs and bottom sheets">
          <AppButton label="Open confirmation dialog" onPress={() => setDialogVisible(true)} variant="secondary" />
          <AppButton label="Open selection sheet" onPress={() => setSheetVisible(true)} variant="secondary" />
        </ShowcaseSection>
        <ShowcaseSection title="Progress indicators">
          <ProgressIndicator label="Campaign readiness" value={68} />
          <ProgressIndicator compact label="Compact progress" value={32} />
          <ProgressIndicator label="Loading example" />
          <ProgressIndicator label="Reduced-motion loading" reduceMotion />
        </ShowcaseSection>
      </ScrollView>
      <AppDialog
        confirmLabel="Remove example"
        description="Destructive confirmation requires an explicit action and remains dismissible with Android back."
        kind="destructive"
        onConfirm={() => setDialogVisible(false)}
        onDismiss={() => setDialogVisible(false)}
        title="Remove this example?"
        visible={dialogVisible}
      />
      <AppBottomSheet
        description="Long selection content scrolls while the dismissal action remains reachable."
        onDismiss={() => setSheetVisible(false)}
        title="Choose an example"
        visible={sheetVisible}
      >
        <AppListItem metadata="Selection example" onPress={() => setSheetVisible(false)} title="Focused mode" />
      </AppBottomSheet>
    </SafeAreaView>
  );
}

export function ShowcaseSection({ children, title }: { children: React.ReactNode; title: string }) {
  const styles = useThemeStyles(createStyles);
  return (
    <View style={styles.section}>
      <AppText accessibilityRole="header" variant="heading2">{title}</AppText>
      <View style={styles.examples}>{children}</View>
    </View>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { backgroundColor: theme.colors.background, flex: 1 },
  content: { padding: spacing.lg, paddingBottom: spacing.xxxl },
  introduction: { marginTop: spacing.sm },
  section: { marginTop: spacing.xl },
  examples: { gap: spacing.sm, marginTop: spacing.md },
});

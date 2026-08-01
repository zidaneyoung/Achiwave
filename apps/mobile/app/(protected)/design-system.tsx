import { useState } from "react";
import { Redirect } from "expo-router";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AppButton } from "../../src/components/AppButton";
import { AppSelector, AppTextField } from "../../src/components/FormControls";
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
      </ScrollView>
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

import type { ReactNode } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";

interface KeyboardAwareScreenProps {
  children: ReactNode;
  contentContainerStyle?: StyleProp<ViewStyle>;
}

export function KeyboardAwareScreen({
  children,
  contentContainerStyle,
}: KeyboardAwareScreenProps) {
  const styles = useThemeStyles(createStyles);
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.flex}
      >
        <ScrollView
          automaticallyAdjustKeyboardInsets={Platform.OS === "ios"}
          contentContainerStyle={contentContainerStyle}
          keyboardDismissMode={Platform.OS === "ios" ? "interactive" : "on-drag"}
          keyboardShouldPersistTaps="handled"
        >
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: theme.colors.background },
  flex: { flex: 1 },
});

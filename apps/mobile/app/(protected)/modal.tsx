import { Text, StyleSheet } from "react-native";

import { ModalScreen } from "../../src/navigation/ModalScreen";
import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../../src/theme/ThemeProvider";

export default function ProtectedModalRoute() {
  const styles = useThemeStyles(createStyles);
  return (
    <ModalScreen
      description="Modal routes are reserved for temporary focused actions. Native back and the explicit Close control both dismiss this surface."
      title="Temporary action"
    >
      <Text style={styles.note}>
        Campaign creation remains deferred to Stage 6.
      </Text>
    </ModalScreen>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  note: { color: theme.colors.accent, fontSize: 14, lineHeight: 20, marginTop: 20 },
});

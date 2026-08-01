import { StyleSheet } from "react-native";

import { ModalScreen } from "../../src/navigation/ModalScreen";
import { useThemeStyles } from "../../src/theme/ThemeProvider";
import { AppText } from "../../src/theme/AppText";
import { spacing } from "../../src/theme/tokens";

export default function ProtectedModalRoute() {
  const styles = useThemeStyles(createStyles);
  return (
    <ModalScreen
      description="Modal routes are reserved for temporary focused actions. Native back and the explicit Close control both dismiss this surface."
      title="Temporary action"
    >
      <AppText tone="accent" variant="label" style={styles.note}>
        Campaign creation remains deferred to Stage 6.
      </AppText>
    </ModalScreen>
  );
}

const createStyles = () => StyleSheet.create({
  note: { marginTop: spacing.md },
});

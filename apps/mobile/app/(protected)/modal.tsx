import { Text, StyleSheet } from "react-native";

import { ModalScreen } from "../../src/navigation/ModalScreen";

export default function ProtectedModalRoute() {
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

const styles = StyleSheet.create({
  note: { color: "#66C0F4", fontSize: 14, lineHeight: 20, marginTop: 20 },
});

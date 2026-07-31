import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuthentication } from "../../src/auth/AuthContext";

export default function ProtectedHomeRoute() {
  const { state } = useAuthentication();
  if (state.status !== "authenticated") {
    return null;
  }
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Signed in
        </Text>
        <Text style={styles.message}>{state.user.email}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#f7f5ef" },
  container: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#17221d", fontSize: 32, fontWeight: "700" },
  message: { color: "#35423b", fontSize: 17, marginTop: 12 },
});

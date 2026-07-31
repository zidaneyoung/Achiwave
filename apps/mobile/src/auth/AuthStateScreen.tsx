import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

interface AuthStateScreenProps {
  title: string;
  message: string;
  loading?: boolean;
}

export function AuthStateScreen({
  title,
  message,
  loading = false,
}: AuthStateScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {loading ? (
          <ActivityIndicator
            accessibilityLabel="Checking authentication"
            color="#1d5b44"
            size="large"
          />
        ) : null}
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        <Text style={styles.message}>{message}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f7f5ef",
  },
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  title: {
    color: "#17221d",
    fontSize: 28,
    fontWeight: "700",
    marginTop: 16,
    textAlign: "center",
  },
  message: {
    color: "#35423b",
    fontSize: 17,
    lineHeight: 24,
    marginTop: 12,
    maxWidth: 380,
    textAlign: "center",
  },
});

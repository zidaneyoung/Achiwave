import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function NotFoundRoute() {
  return (
    <SafeAreaView edges={["left", "right", "bottom"]} style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          This route does not exist.
        </Text>
        <Link accessibilityRole="link" href="/" style={styles.link}>
          Return to Achiwave
        </Link>
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
    fontSize: 24,
    fontWeight: "700",
    textAlign: "center",
  },
  link: {
    color: "#1d5b44",
    fontSize: 17,
    marginTop: 20,
    textDecorationLine: "underline",
  },
});

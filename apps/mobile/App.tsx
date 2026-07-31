import { SafeAreaView, StatusBar, StyleSheet, Text, View } from "react-native";

export default function App() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text accessibilityRole="header" style={styles.title}>
          Achiwave
        </Text>
        <Text style={styles.subtitle}>Mobile foundation ready.</Text>
        <StatusBar barStyle="dark-content" />
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
    fontSize: 32,
    fontWeight: "700",
  },
  subtitle: {
    color: "#46534c",
    fontSize: 17,
    marginTop: 8,
  },
});

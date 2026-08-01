import { useEffect, useRef } from "react";
import { Animated, StyleSheet, View } from "react-native";

import {
  type AchiwaveTheme,
  useThemeStyles,
} from "../theme/ThemeProvider";
import { radii, sizing, spacing } from "../theme/tokens";

export type SkeletonLayout = "text" | "card" | "list" | "profile";

export function LoadingSkeleton({
  layout = "card",
  reduceMotion = false,
  label = "Loading content",
}: {
  layout?: SkeletonLayout;
  reduceMotion?: boolean;
  label?: string;
}) {
  const styles = useThemeStyles(createStyles);
  const opacity = useRef(new Animated.Value(0.55)).current;

  useEffect(() => {
    if (reduceMotion) {
      opacity.setValue(0.7);
      return;
    }
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { duration: 700, toValue: 0.9, useNativeDriver: true }),
        Animated.timing(opacity, { duration: 700, toValue: 0.55, useNativeDriver: true }),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [opacity, reduceMotion]);

  return (
    <View accessibilityLabel={label} accessibilityRole="progressbar">
      <Animated.View
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        style={[styles.group, { opacity }]}
      >
        {layout === "profile" ? <View style={styles.avatar} /> : null}
        <View style={styles.lineWide} />
        <View style={styles.lineMedium} />
        {layout === "card" || layout === "list" ? <View style={styles.lineShort} /> : null}
        {layout === "card" ? <View style={styles.cardBody} /> : null}
      </Animated.View>
    </View>
  );
}

const createStyles = (theme: AchiwaveTheme) => StyleSheet.create({
  group: { gap: spacing.xs },
  lineWide: { backgroundColor: theme.colors.surfaceElevated, borderRadius: radii.sm, height: spacing.md, width: "92%" },
  lineMedium: { backgroundColor: theme.colors.surfaceElevated, borderRadius: radii.sm, height: spacing.sm, width: "70%" },
  lineShort: { backgroundColor: theme.colors.surfaceElevated, borderRadius: radii.sm, height: spacing.sm, width: "42%" },
  cardBody: { backgroundColor: theme.colors.surfaceElevated, borderRadius: radii.md, height: sizing.skeletonBody, marginTop: spacing.xs },
  avatar: { backgroundColor: theme.colors.surfaceElevated, borderRadius: radii.pill, height: sizing.skeletonAvatar, marginBottom: spacing.xs, width: sizing.skeletonAvatar },
});

import React from "react";
import { StyleSheet, View } from "react-native";
import Svg, { Path } from "react-native-svg";
import { colors } from "@/src/theme";
import { T } from "./ui";

export function BrandMark({ testID = "brand-mark" }: { testID?: string }) {
  return <View testID={testID} style={styles.row} accessibilityLabel="Jeelive.ai — Score 200+ with AI">
    <Svg width={36} height={44} viewBox="0 0 36 44">
      <Path d="M18 3 L32 7 L30 29 L18 40 L6 31 L3 20 L9 16 L10 10 Z" fill={colors.brandTertiary} stroke={colors.brandText} strokeWidth={2} />
      <Path d="M12 14 L25 10 L24 28 L18 33 L11 27" fill="none" stroke={colors.brandPrimary} strokeWidth={4} strokeLinejoin="round" />
    </Svg>
    <View><T testID={`${testID}-name`} w="heavy" size={24} style={styles.name}>Jeelive.ai</T>
      <T testID={`${testID}-tagline`} w="heavy" size={8} color={colors.brandText} style={styles.tagline}>SCORE 200+ WITH AI</T>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 6 },
  name: { letterSpacing: -0.8, lineHeight: 27 },
  tagline: { letterSpacing: 0.8, lineHeight: 12 },
});
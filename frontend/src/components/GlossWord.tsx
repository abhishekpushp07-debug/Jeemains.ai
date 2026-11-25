// A word in glossy yellow on a red card (Home's Misfire and Matched cards): deep yellow letters with a dark shade under
// them, and their upper half in a paler yellow (the light on them).
import React from "react";
import { PixelRatio, StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { colors } from "@/src/theme";

export function GlossWord({ children, testID, size = 19 }: { children: string; testID: string; size?: number }) {
  const line = Math.round(size * 1.37);
  const face = { lineHeight: line, letterSpacing: 1.5 };
  // The paler copy is cut off at half the line's height; text grows with the phone's font size (T stops at 1.6), so the cut does too.
  const half = line * 0.5 * Math.min(PixelRatio.getFontScale(), 1.6);
  return <View>
    <T testID={testID} w="heavy" size={size} color={colors.custom_glossYellow} numberOfLines={1} style={[face, styles.shade]}>{children}</T>
    <View pointerEvents="none" aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={[styles.light, { height: half }]}>
      <T w="heavy" size={size} color={colors.custom_glossYellowHi} numberOfLines={1} style={face}>{children}</T>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  shade: { textShadowColor: colors.custom_glossYellowShade, textShadowOffset: { width: 0, height: 1.5 }, textShadowRadius: 2 },
  light: { position: "absolute", left: 0, right: 0, top: 0, overflow: "hidden" },
});

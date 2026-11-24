// The blood-red "Analysis" button on the series day cards: a glossy blood-red face, a glass glint that crosses from corner
// to corner and five colours (ruby, gold, white, rose, flame) running round its edge. Opens the day's analysis.
import React from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { Shine } from "@/src/analysis/Shine";
import { bloodEdge, colors, space } from "@/src/theme";

const BLOOD = [colors.custom_chipBlood, colors.custom_chipBloodDeep] as const;

/** `big` = the today card's button, which carries the marks themselves. */
export function AnalysisButton({ onPress, testID, label = "Analysis dekho", note, big }: { onPress: () => void; testID: string; label?: string; note?: string; big?: boolean }) {
  return <Press testID={testID} onPress={onPress} accessibilityRole="button" accessibilityLabel={note ? `${label}. ${note}` : label} scaleTo={0.97} style={styles.wrap}>
    <Shine radius={14} ring={2} tones={BLOOD} edge={bloodEdge} gloss={colors.custom_chipBloodGloss} glint={colors.custom_chipBloodGlint}
      band={46} part={40} corner face={[styles.face, big && styles.big]}>
      <Icon name="chart-donut" size={big ? 20 : 16} color={colors.custom_chipBloodInk} />
      <View style={{ flexShrink: 1 }}>
        <T w="heavy" size={big ? 16 : 13} color={colors.custom_chipBloodInk} numberOfLines={1}>{label}</T>
        {note ? <T w={big ? "bold" : undefined} size={big ? 11.5 : 10.5} color={colors.custom_chipBloodSoft} numberOfLines={1}>{note}</T> : null}
      </View>
    </Shine>
  </Press>;
}

const styles = StyleSheet.create({
  wrap: { borderRadius: 14, alignSelf: "flex-start" },
  face: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 44, paddingHorizontal: 16, paddingVertical: 9 },
  big: { minHeight: 54, paddingHorizontal: 18, gap: space.md },
});

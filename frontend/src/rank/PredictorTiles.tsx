// The two tools of the Rank tab as big tiles, in the Home screen's exam-tile shape: Rank predictor first, College predictor next.
// The chosen tile turns into a small piece of the Rank Card (brushed graphite, blood-red glow, silver-red top edge).
import React from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";

export type Tool = "rank" | "college";
const TILES: { key: Tool; icon: IconName; title: string; value: string; badge?: string }[] = [
  { key: "rank", icon: "podium", title: "RANK PREDICTOR", value: "rank + percentile", badge: "NEW" },
  { key: "college", icon: "school-outline", title: "COLLEGE PREDICTOR", value: "colleges + cutoffs" },
];
const EDGE = [colors.custom_clear, colors.custom_rankBlood, colors.custom_rankShimmer, colors.custom_rankBlood, colors.custom_clear] as const;

export function PredictorTiles({ value, onChange }: { value: Tool; onChange: (t: Tool) => void }) {
  const narrow = useWindowDimensions().width < 360;
  return <View accessibilityRole="tablist" style={styles.row}>
    {TILES.map(t => {
      const on = t.key === value;
      return <Press key={t.key} testID={`rank-tool-${t.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${t.title}. ${t.value}`}
        onPress={() => onChange(t.key)} scaleTo={0.97} style={styles.press}>
        <View style={[styles.tile, narrow && styles.tileNarrow, on && styles.tileOn]}>
          <LinearGradient colors={on ? [colors.custom_rankFrom, colors.custom_rankMid, colors.custom_rankTo] : [colors.custom_cardRaised, colors.custom_card]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
          {on ? <>
            <LinearGradient colors={[colors.custom_clear, colors.custom_rankGlow]} start={{ x: 0.3, y: 0.2 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
            <LinearGradient colors={EDGE} locations={[0, 0.22, 0.5, 0.78, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.edge} />
          </> : null}
          <View style={styles.top}>
            <View style={[styles.icon, narrow && styles.iconNarrow, on && styles.iconOn]}>
              <Glyph name={t.icon} size={narrow ? 21 : 24} color={on ? colors.custom_rankSilver : colors.custom_softText} stroke={1.4} />
            </View>
            {t.badge ? <View style={styles.badge}><T w="bold" size={9.5} color={colors.custom_rankBloodInk} style={{ letterSpacing: 1.2 }}>{t.badge}</T></View> : null}
          </View>
          <View style={{ flex: 1 }} />
          <T testID={`rank-tool-${t.key}-title`} w="heavy" size={narrow ? 13.5 : 15} color={on ? colors.custom_rankBloodInk : colors.custom_softText} style={styles.title} numberOfLines={2}>{t.title}</T>
          <View style={styles.valueRow}>
            <T w="semibold" size={narrow ? 11.5 : 12.5} color={on ? colors.custom_rankSilver : colors.muted} numberOfLines={1} style={{ flexShrink: 1 }}>{t.value}</T>
            <Glyph name="chevron-right" size={14} color={colors.muted} />
          </View>
        </View>
      </Press>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: space.md },
  press: { flex: 1, minWidth: 0 },
  tile: { height: 150, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLineStrong, padding: space.lg, paddingBottom: 14, overflow: "hidden", gap: 4 },
  tileNarrow: { height: 138, padding: 12 },
  tileOn: { borderColor: colors.custom_rankSilverLine, shadowColor: colors.custom_rankBlood, shadowOpacity: 0.35, shadowRadius: 18, shadowOffset: { width: 0, height: 8 }, elevation: 8 },
  edge: { position: "absolute", top: 0, left: 0, right: 0, height: 1.5 },
  top: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 4 },
  icon: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  iconNarrow: { width: 40, height: 40, borderRadius: 20 },
  iconOn: { backgroundColor: colors.custom_rankMid, borderColor: colors.custom_rankSilverLine },
  badge: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3, backgroundColor: colors.custom_rankBloodSoft },
  title: { letterSpacing: 0.8 },
  valueRow: { flexDirection: "row", alignItems: "center", gap: 2 },
});

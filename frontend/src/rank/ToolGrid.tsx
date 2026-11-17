// The Rank tab's five tools as Home-style tiles: two per row, College compare across the bottom.
// The chosen tile turns into a small piece of the Rank Card (brushed graphite, blood-red glow, silver-red top edge).
import React from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";

export type Tool = "rank" | "pct" | "target" | "college" | "compare";
type Tile = { key: Tool; icon: IconName; title: string; value: string; badge?: string };
const ROWS: Tile[][] = [
  [{ key: "rank", icon: "podium", title: "RANK PREDICTOR", value: "marks se rank" },
   { key: "pct", icon: "chart-line-variant", title: "PERCENTILE SE RANK", value: "NTA percentile", badge: "NEW" }],
  [{ key: "target", icon: "bullseye-arrow", title: "TARGET MARKS", value: "college ke liye", badge: "NEW" },
   { key: "college", icon: "school-outline", title: "COLLEGE PREDICTOR", value: "colleges + cutoffs" }],
  [{ key: "compare", icon: "compare-horizontal", title: "COLLEGE COMPARE", value: "saved colleges side by side", badge: "NEW" }],
];
const EDGE = [colors.custom_clear, colors.custom_rankBlood, colors.custom_rankShimmer, colors.custom_rankBlood, colors.custom_clear] as const;

export function ToolGrid({ value, onChange, saved }: { value: Tool; onChange: (t: Tool) => void; saved: number }) {
  const narrow = useWindowDimensions().width < 360;
  return <View accessibilityRole="tablist" style={styles.grid}>
    {ROWS.map((row, r) => <View key={r} style={styles.row}>
      {row.map(t => <ToolTile key={t.key} t={t} on={t.key === value} narrow={narrow} onPress={() => onChange(t.key)}
        value={t.key === "compare" && saved ? `${saved} saved · side by side` : t.value} />)}
    </View>)}
  </View>;
}

function ToolTile({ t, on, narrow, value, onPress }: { t: Tile; on: boolean; narrow: boolean; value: string; onPress: () => void }) {
  return <Press testID={`rank-tool-${t.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${t.title}. ${value}`}
    onPress={onPress} scaleTo={0.97} style={styles.press}>
    <View style={[styles.tile, narrow && styles.tileNarrow, on && styles.tileOn]}>
      <LinearGradient colors={on ? [colors.custom_rankFrom, colors.custom_rankMid, colors.custom_rankTo] : [colors.custom_cardRaised, colors.custom_card]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
      {on ? <>
        <LinearGradient colors={[colors.custom_clear, colors.custom_rankGlow]} start={{ x: 0.3, y: 0.2 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
        <LinearGradient colors={EDGE} locations={[0, 0.22, 0.5, 0.78, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.edge} />
      </> : null}
      <View style={[styles.icon, narrow && styles.iconNarrow, on && styles.iconOn]}>
        <Glyph name={t.icon} size={narrow ? 17 : 20} color={on ? colors.custom_rankSilver : colors.custom_softText} stroke={1.5} />
        {t.badge && !on ? <View testID={`rank-tool-${t.key}-badge`} style={styles.badge}><T w="bold" size={8} color={colors.custom_rankBloodInk} style={{ letterSpacing: 0.8 }}>{t.badge}</T></View> : null}
      </View>
      <View style={{ flex: 1, gap: 2 }}>
        <T testID={`rank-tool-${t.key}-title`} w="heavy" size={narrow ? 11 : 12.5} color={on ? colors.custom_rankBloodInk : colors.custom_softText}
          style={styles.title} numberOfLines={2}>{t.title}</T>
        <T w="semibold" size={narrow ? 10.5 : 11.5} color={on ? colors.custom_rankSilver : colors.muted} numberOfLines={2}>{value}</T>
      </View>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  grid: { gap: space.sm },
  row: { flexDirection: "row", gap: space.sm },
  press: { flex: 1, minWidth: 0 },
  tile: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 72, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong,
    paddingHorizontal: 12, paddingVertical: 10, overflow: "hidden" },
  tileNarrow: { gap: 8, paddingHorizontal: 9, minHeight: 66 },
  tileOn: { borderColor: colors.custom_rankSilverLine },
  edge: { position: "absolute", top: 0, left: 0, right: 0, height: 1.5 },
  icon: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  iconNarrow: { width: 32, height: 32, borderRadius: 16 },
  iconOn: { backgroundColor: colors.custom_rankMid, borderColor: colors.custom_rankSilverLine },
  title: { letterSpacing: 0.6 },
  // Sits on the icon's bottom edge, so it never covers the title.
  badge: { position: "absolute", bottom: -7, alignSelf: "center", borderRadius: 999, paddingHorizontal: 4, paddingVertical: 1,
    backgroundColor: colors.custom_rankBloodSoft, borderWidth: 1, borderColor: colors.custom_rankBlood },
});

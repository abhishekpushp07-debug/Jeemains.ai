// The Rank tab's five tools as Home-style tiles: two per row, College compare across the bottom.
// Every tile is its own black-metal card with a diamond in the corner: maroon, indigo, teal, pink and champagne.
// The chosen tile glows brighter, its diamond sparkles and it gets the jewel's top edge.
import React from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, space } from "@/src/theme";
import { Jewel, JEWELS, MetalFace } from "./Metal";

export type Tool = "rank" | "pct" | "target" | "college" | "compare";
type Tile = { key: Tool; icon: IconName; title: string; value: string; badge?: string };
const ROWS: Tile[][] = [
  [{ key: "rank", icon: "podium", title: "RANK PREDICTOR", value: "marks se rank" },
   { key: "pct", icon: "chart-line-variant", title: "PERCENTILE SE RANK", value: "NTA percentile", badge: "NEW" }],
  [{ key: "target", icon: "bullseye-arrow", title: "TARGET MARKS", value: "college ke liye", badge: "NEW" },
   { key: "college", icon: "school-outline", title: "COLLEGE PREDICTOR", value: "colleges + cutoffs" }],
  [{ key: "compare", icon: "compare-horizontal", title: "COLLEGE COMPARE", value: "saved colleges side by side", badge: "NEW" }],
];
/** Each tool's own colour. */
const TOOL_JEWEL: Record<Tool, Jewel> = { rank: "maroon", pct: "indigo", target: "teal", college: "pink", compare: "champ" };

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
  const jewel = TOOL_JEWEL[t.key], j = JEWELS[jewel];
  return <Press testID={`rank-tool-${t.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${t.title}. ${value}`}
    onPress={onPress} scaleTo={0.97} style={[styles.press, on && [styles.pressOn, { shadowColor: j.glow }]]}>
    <View style={[styles.tile, narrow && styles.tileNarrow, on && { borderColor: j.line }]}>
      <MetalFace jewel={jewel} on={on} />
      <View style={[styles.icon, narrow && styles.iconNarrow, on && { borderColor: j.line, backgroundColor: j.soft }]}>
        <Glyph name={t.icon} size={narrow ? 15 : 17} color={j.ink} stroke={1.4} />
        {t.badge && !on ? <View testID={`rank-tool-${t.key}-badge`} style={[styles.badge, { borderColor: j.line }]}>
          <T w="bold" size={8} color={j.ink} style={{ letterSpacing: 0.8 }}>{t.badge}</T>
        </View> : null}
      </View>
      <View style={{ flex: 1, gap: 3 }}>
        <T testID={`rank-tool-${t.key}-title`} w="semibold" size={narrow ? 9.5 : 10.5} color={on ? j.ink : colors.custom_rankSilver}
          style={styles.title} numberOfLines={2}>{t.title}</T>
        {/* Right padding keeps the small line clear of the corner diamond. */}
        <T size={narrow ? 9.5 : 10.5} color={on ? colors.custom_rankSilver : colors.muted} numberOfLines={1} style={{ paddingRight: narrow ? 0 : 16 }}>{value}</T>
      </View>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  grid: { gap: space.sm },
  row: { flexDirection: "row", gap: space.sm },
  press: { flex: 1, minWidth: 0, borderRadius: 18 },
  pressOn: { shadowOpacity: 0.55, shadowRadius: 16, shadowOffset: { width: 0, height: 6 } },
  tile: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 64, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_metalEdge,
    backgroundColor: colors.custom_metalMid, paddingHorizontal: 12, paddingVertical: 10, overflow: "hidden" },
  tileNarrow: { gap: 8, paddingHorizontal: 9, minHeight: 60 },
  icon: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  iconNarrow: { width: 28, height: 28, borderRadius: 14 },
  title: { letterSpacing: 1.2 },
  // Sits on the icon's bottom edge, so it never covers the title.
  badge: { position: "absolute", bottom: -7, alignSelf: "center", borderRadius: 999, paddingHorizontal: 4, paddingVertical: 1,
    backgroundColor: colors.custom_rankBg, borderWidth: 1 },
});

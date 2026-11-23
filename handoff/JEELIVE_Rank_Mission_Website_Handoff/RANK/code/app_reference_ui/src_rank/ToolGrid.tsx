// The Rank tab's six tools as Home-style tiles, two per row, on the black page.
// Every tile is its tool's own colour (maroon, indigo, teal, blood red, gold, violet) with a diamond in the corner, a soft
// gloss, a glass glint that crosses from corner to corner and three matching colours running round its edge.
// The chosen tile glows in its form's bright colour, and that colour and white run round its thicker edge: the same colour
// the form below wears.
import React from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { Shine } from "@/src/analysis/Shine";
import { rankColors as colors, space } from "@/src/theme";
import { Jewel, JEWELS, JewelFace } from "./JewelFace";
import { ACCENTS } from "./accent";

export type Tool = "rank" | "cutoff" | "target" | "college" | "compare" | "dream";
type Tile = { key: Tool; icon: IconName; title: string; value: string; badge?: string };
const ROWS: Tile[][] = [
  [{ key: "rank", icon: "podium", title: "RANK PREDICTOR", value: "marks se rank" },
   { key: "cutoff", icon: "format-list-checks", title: "CUT OFF", value: "college / branch", badge: "NEW" }],
  [{ key: "target", icon: "bullseye-arrow", title: "TARGET MARKS", value: "college ke liye", badge: "NEW" },
   { key: "college", icon: "school-outline", title: "COLLEGE PREDICTOR", value: "colleges + cutoffs" }],
  [{ key: "compare", icon: "compare-horizontal", title: "COLLEGE COMPARE", value: "side by side", badge: "NEW" },
   { key: "dream", icon: "star-shooting-outline", title: "DREAM COLLEGE", value: "kitne marks door", badge: "NEW" }],
];
/** Each tool's own colour. */
const TOOL_JEWEL: Record<Tool, Jewel> = { rank: "maroon", cutoff: "indigo", target: "teal", college: "blood", compare: "champ", dream: "violet" };

/** The chosen tile's edge: its form's colour and white, chasing each other. */
const CHOSEN_EDGE = Object.fromEntries((Object.keys(TOOL_JEWEL) as Tool[]).map(k => [k, [ACCENTS[k].text, colors.custom_tileInk, ACCENTS[k].text, colors.custom_tileInk, ACCENTS[k].text]])) as unknown as Record<Tool, readonly [string, string, ...string[]]>;

export function ToolGrid({ value, onChange, saved, colleges, dreams }: { value: Tool; onChange: (t: Tool) => void; saved: number; colleges: number; dreams: number }) {
  const narrow = useWindowDimensions().width < 360;
  const compare = [colleges ? `${colleges} college` : null, saved ? `${saved} branch` : null].filter(Boolean).join(" · ");
  const valueOf = (t: Tile) => t.key === "compare" && compare ? compare : t.key === "dream" && dreams ? `${dreams} dream chune` : t.value;
  return <View accessibilityRole="tablist" style={styles.grid}>
    {ROWS.map((row, r) => <View key={r} style={styles.row}>
      {row.map((t, c) => <ToolTile key={t.key} t={t} on={t.key === value} narrow={narrow} order={r * 2 + c} onPress={() => onChange(t.key)} value={valueOf(t)} />)}
    </View>)}
  </View>;
}

function ToolTile({ t, on, narrow, value, order, onPress }: { t: Tile; on: boolean; narrow: boolean; value: string; order: number; onPress: () => void }) {
  const jewel = TOOL_JEWEL[t.key], j = JEWELS[jewel];
  return <Press testID={`rank-tool-${t.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${t.title}. ${value}`}
    onPress={onPress} scaleTo={0.97} style={[styles.press, { backgroundColor: j.to }, on && { ...glow, shadowColor: ACCENTS[t.key].text }]}>
    {/* The glint reaches each tile a little after the one before it. */}
    <Shine fill radius={18} ring={on ? 3 : 2} backdrop={<JewelFace jewel={jewel} on={on} />} edge={on ? CHOSEN_EDGE[t.key] : j.edge} gloss={j.gloss} glint={j.glint}
      band={30} part={40} corner delay={order * 200} face={[on ? styles.tileOn : styles.tile, narrow && (on ? styles.tileOnNarrow : styles.tileNarrow)]}>
      <View style={[styles.icon, narrow && styles.iconNarrow, { backgroundColor: j.chip, borderColor: j.line }]}>
        <Glyph name={t.icon} size={narrow ? 15 : 17} color={j.ink} stroke={1.4} />
        {t.badge && !on ? <View testID={`rank-tool-${t.key}-badge`} style={styles.badge}>
          <T w="bold" size={8} color={j.badge} style={{ letterSpacing: 0.8 }}>{t.badge}</T>
        </View> : null}
      </View>
      <View style={{ flex: 1, gap: 3 }}>
        <T testID={`rank-tool-${t.key}-title`} w="semibold" size={narrow ? 9.5 : 10.5} color={j.ink} style={styles.title} numberOfLines={2}>{t.title}</T>
        {/* Right padding keeps the small line clear of the corner diamond. */}
        <T size={narrow ? 9.5 : 10.5} color={j.soft} numberOfLines={1} style={{ paddingRight: narrow ? 0 : 16 }}>{value}</T>
      </View>
    </Shine>
  </Press>;
}

/** The chosen tile's glow; kept in one inline style with its colour so web draws the blur and Android gets elevation. */
const glow = { shadowOpacity: 0.7, shadowRadius: 18, shadowOffset: { width: 0, height: 4 }, elevation: 10 };

const styles = StyleSheet.create({
  grid: { gap: space.sm },
  row: { flexDirection: "row", gap: space.sm },
  press: { flex: 1, minWidth: 0, borderRadius: 18 },
  // A tile is 64 high (60 on small phones), as before: 60 inside its 2-point edge, or 58 inside the chosen tile's 3-point edge.
  tile: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 60, paddingHorizontal: 11, paddingVertical: 9 },
  tileOn: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 10, paddingVertical: 8 },
  tileNarrow: { gap: 8, paddingHorizontal: 8, minHeight: 56 },
  tileOnNarrow: { gap: 8, paddingHorizontal: 7, minHeight: 54 },
  icon: { width: 34, height: 34, borderRadius: 17, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  iconNarrow: { width: 28, height: 28, borderRadius: 14 },
  title: { letterSpacing: 1.2 },
  // Sits on the icon's bottom edge, so it never covers the title.
  badge: { position: "absolute", bottom: -7, alignSelf: "center", borderRadius: 999, paddingHorizontal: 5, paddingVertical: 1, backgroundColor: colors.custom_tileBadge },
});

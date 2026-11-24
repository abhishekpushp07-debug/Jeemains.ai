// The two card looks of the All India series, kept in one place so every card that wears one is exactly the same card:
// Home's onyx-into-ruby All India card, and the series page's glossy baby pink streak card.
import React, { useId } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";
import { Glyph } from "@/src/components/Glyph";
import { IconName, T } from "@/src/components/ui";
import { colors, pastel, seriesEdge, space, tabEdges } from "@/src/theme";

/** The face of Home's All India card: onyx into ruby, a red glow from the top right corner and a hairline sheen along the top. */
export function SeriesBackdrop() {
  const glow = "seriesGlow" + useId().replace(/[^a-z0-9]/gi, "");
  return <>
    <LinearGradient colors={[colors.custom_seriesFrom, colors.custom_seriesMid, colors.custom_seriesTo]} locations={[0, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    {/* Explicit stopOpacity: native SVG ignores alpha inside stopColor. */}
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" pointerEvents="none">
      <Defs>
        <RadialGradient id={glow} cx="96%" cy="0%" rx="75%" ry="65%" fx="96%" fy="0%">
          <Stop offset="0" stopColor={colors.custom_seriesGlow} stopOpacity={0.45} />
          <Stop offset="1" stopColor={colors.custom_seriesGlow} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect x="0" y="0" width="100%" height="100%" fill={`url(#${glow})`} />
    </Svg>
    <LinearGradient colors={[colors.custom_clear, colors.custom_seriesSheen, colors.custom_clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.sheen} pointerEvents="none" />
  </>;
}

/** What goes round and over that face: ruby, gold and rose run round its edge; a soft gloss; a glass glint from corner to corner. */
export const onyxShine = { ring: 2, edge: seriesEdge, gloss: colors.custom_seriesGloss, glint: colors.custom_seriesGlint, band: 96, part: 46, corner: true } as const;

/** The streak card: two baby pinks that change places slowly; rose, orchid and coral run round its edge; a white gloss and a white corner-to-corner glint. */
export const pinkShine = {
  ring: 2, tones: [colors.custom_seriesPink, colors.custom_seriesPinkDeep], edge: tabEdges.pink,
  gloss: colors.custom_seriesPastelGloss, glint: colors.custom_seriesPastelGlint, band: 84, part: 46, corner: true,
} as const;

const softShine = { ring: 2, gloss: colors.custom_seriesPastelGloss, glint: colors.custom_seriesPastelGlint, band: 72, part: 46, corner: true } as const;

/** The score trend card: two sky blues that change places slowly; azure, indigo and periwinkle run round its edge. Its line is royal blue. */
export const skyShine = { ...softShine, tones: [colors.custom_tabSkySoft, colors.custom_tabSkySoftDeep], edge: tabEdges.sky } as const;

/** The day map card: warm sand, so the green and red days stand out; Home's ruby, gold and rose run round its edge. */
export const sandShine = { ...softShine, tones: [pastel.missed.from, pastel.missed.to], edge: seriesEdge } as const;

/** "Nothing here yet" on a soft glossy card: the hairline icon on a white circle, a title and a sentence, in the dark inks that read on every soft colour. */
export function SoftEmpty({ icon, title, body, action }: { icon: IconName; title: string; body: string; action?: React.ReactNode }) {
  return <View style={styles.empty}>
    <View style={styles.emptyIcon}><Glyph name={icon} size={28} color={colors.custom_tabInk} stroke={1.5} /></View>
    <T w="bold" size={17} color={colors.custom_tabInk} style={styles.center}>{title}</T>
    <T size={13} color={colors.custom_tabInkSoft} style={styles.center}>{body}</T>
    {action}
  </View>;
}

const styles = StyleSheet.create({
  sheen: { position: "absolute", top: 0, left: 28, right: 28, height: 1 },
  center: { textAlign: "center" },
  empty: { alignItems: "center", padding: space.xl - 2, gap: space.sm },
  emptyIcon: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_tabChip },
});

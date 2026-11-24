// The two card looks of the All India series, kept in one place so every card that wears one is exactly the same card:
// Home's onyx-into-ruby All India card, and the series page's glossy baby pink streak card.
import React, { useId } from "react";
import { StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";
import { colors, seriesEdge, tabEdges } from "@/src/theme";

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

const styles = StyleSheet.create({
  sheen: { position: "absolute", top: 0, left: 28, right: 28, height: 1 },
});

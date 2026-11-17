// The face of each Rank tool tile, after a black metal membership card: brushed graphite mixed into the tool's own colour
// (maroon, indigo, teal, pink or champagne), fine brush lines, a broad diagonal sheen, a bevelled top edge, a soft light
// behind a faceted diamond in the corner, and on the chosen tile a brighter glow with a jewel top edge. Gradients and SVG only.
import React, { useId } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Defs, Pattern, RadialGradient, Rect, Stop } from "react-native-svg";
import { rankColors as colors } from "@/src/theme";
import { Diamond } from "./Diamond";

export type Jewel = "maroon" | "indigo" | "teal" | "pink" | "champ";
type Tone = { from: string; mid: string; to: string; glow: string; glow2?: string; line: string; ink: string; soft: string };
export const JEWELS: Record<Jewel, Tone> = {
  maroon: { from: colors.custom_maroonFrom, mid: colors.custom_maroonMid, to: colors.custom_maroonTo, glow: colors.custom_maroonGlow, line: colors.custom_maroonLine,
    ink: colors.custom_maroonInk, soft: colors.custom_maroonSoft },
  indigo: { from: colors.custom_indigoFrom, mid: colors.custom_indigoMid, to: colors.custom_indigoTo, glow: colors.custom_indigoGlow, glow2: colors.custom_indigoGlow2,
    line: colors.custom_indigoLine, ink: colors.custom_indigoInk, soft: colors.custom_indigoSoft },
  teal: { from: colors.custom_tealFrom, mid: colors.custom_tealMid, to: colors.custom_tealTo, glow: colors.custom_tealGlow, line: colors.custom_tealLine,
    ink: colors.custom_tealInk, soft: colors.custom_tealSoft },
  pink: { from: colors.custom_pinkFrom, mid: colors.custom_pinkMid, to: colors.custom_pinkTo, glow: colors.custom_pinkGlow, line: colors.custom_pinkLine,
    ink: colors.custom_pinkInk, soft: colors.custom_pinkSoft },
  champ: { from: colors.custom_champFrom, mid: colors.custom_champMid, to: colors.custom_champTo, glow: colors.custom_champGlow, line: colors.custom_champLine,
    ink: colors.custom_champInk, soft: colors.custom_champSoft },
};

// Brush lines: one tiny tile of thin light and dark streaks repeated down the card, so the texture costs one shape.
const STREAKS = [
  { y: 0.4, h: 0.7, o: 0.05, dark: false }, { y: 2.6, h: 0.6, o: 0.05, dark: true }, { y: 4.3, h: 0.8, o: 0.035, dark: false },
  { y: 6.4, h: 0.5, o: 0.04, dark: true }, { y: 8.1, h: 0.7, o: 0.03, dark: false }, { y: 10.2, h: 0.6, o: 0.045, dark: true },
];
const STREAK_TILE = 12;

export function MetalFace({ jewel, on }: { jewel: Jewel; on?: boolean }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const j = JEWELS[jewel];
  const strength = on ? 0.75 : 0.45;
  return <View pointerEvents="none" style={StyleSheet.absoluteFill}>
    <LinearGradient colors={[j.from, j.mid, j.to]} locations={[0, 0.45, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <Svg width="100%" height="100%" style={StyleSheet.absoluteFill}>
      <Defs>
        <Pattern id={`p${id}`} patternUnits="userSpaceOnUse" x="0" y="0" width="16" height={STREAK_TILE}>
          {STREAKS.map(s => <Rect key={s.y} x="0" y={s.y} width="16" height={s.h} fill={s.dark ? colors.custom_rankBg : colors.custom_rankSparkle} fillOpacity={s.o} />)}
        </Pattern>
        <RadialGradient id={`g${id}`} cx="86%" cy="62%" r="62%">
          <Stop offset="0" stopColor={j.glow} stopOpacity={strength} />
          <Stop offset="1" stopColor={j.glow} stopOpacity={0} />
        </RadialGradient>
        {j.glow2 ? <RadialGradient id={`h${id}`} cx="12%" cy="105%" r="55%">
          <Stop offset="0" stopColor={j.glow2} stopOpacity={strength * 0.8} />
          <Stop offset="1" stopColor={j.glow2} stopOpacity={0} />
        </RadialGradient> : null}
      </Defs>
      <Rect x="0" y="0" width="100%" height="100%" fill={`url(#g${id})`} />
      {j.glow2 ? <Rect x="0" y="0" width="100%" height="100%" fill={`url(#h${id})`} /> : null}
      <Rect x="0" y="0" width="100%" height="100%" fill={`url(#p${id})`} />
    </Svg>
    <Diamond width={46} tint={j.ink} sparkle={on} opacity={on ? 0.7 : 0.35} style={styles.gem} />
    <LinearGradient colors={[colors.custom_clear, colors.custom_metalSheenSoft, colors.custom_metalSheen, colors.custom_metalSheenSoft, colors.custom_clear]}
      locations={[0.2, 0.38, 0.48, 0.58, 0.76]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={[colors.custom_clear, colors.custom_metalShade]} locations={[0.55, 1]} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={on ? [colors.custom_clear, j.line, colors.custom_rankShimmer, j.line, colors.custom_clear] : [colors.custom_clear, colors.custom_metalBevel, colors.custom_metalSheen, colors.custom_clear]}
      start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.edge, on && styles.edgeOn]} />
  </View>;
}

const styles = StyleSheet.create({
  gem: { position: "absolute", right: -8, bottom: -9 },
  edge: { position: "absolute", top: 0, left: 0, right: 0, height: 1 },
  edgeOn: { height: 1.5 },
});

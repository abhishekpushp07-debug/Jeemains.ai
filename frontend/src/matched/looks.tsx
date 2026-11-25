// The Matched look, kept in one place for Home's card, the sign-in screen's bar and the top cards of Matched: glossy
// red into deep red with a yellow glow in the top right corner; aqua, violet-blue and white (the opposites of red and
// yellow) run round its edge; a soft gloss; a glass glint from corner to corner; fireworks; and the golden cup.
import React, { useEffect, useId } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useSharedValue, withDelay, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle, Defs, Line, Path, RadialGradient, Rect, Stop } from "react-native-svg";
import { CALM, STILL, useShineLevel } from "@/src/analysis/smooth";
import { useStill } from "@/src/motion";
import { Alive } from "@/src/rapid/Art";
import { colors, matchedEdge } from "@/src/theme";

export function MatchedBackdrop() {
  const glow = "matchedGlow" + useId().replace(/[^a-z0-9]/gi, "");
  return <>
    <LinearGradient pointerEvents="none" colors={[colors.custom_matchedFrom, colors.custom_matchedMid, colors.custom_matchedTo]} locations={[0, 0.55, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    {/* Explicit stopOpacity: native SVG ignores alpha inside stopColor. */}
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" pointerEvents="none">
      <Defs>
        <RadialGradient id={glow} cx="94%" cy="4%" rx="58%" ry="78%" fx="94%" fy="4%">
          <Stop offset="0" stopColor={colors.custom_glossYellow} stopOpacity={0.6} />
          <Stop offset="1" stopColor={colors.custom_glossYellow} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect x="0" y="0" width="100%" height="100%" fill={`url(#${glow})`} />
    </Svg>
  </>;
}

/** What goes round and over that face (a plain running edge, no dots). */
export const matchedShine = { ring: 3, edge: matchedEdge, gloss: colors.custom_fireGloss, glint: colors.custom_fireGlint, band: 96, part: 46, corner: true } as const;

const RAYS = Array.from({ length: 14 }, (_, i) => (i / 14) * Math.PI * 2);
/** Where a firework bursts (share of the card's width and height), how big it is, its colour, and how long after the first. */
export type Sky = [number, number, number, string, number][];
// The biggest one opens behind the cup (it stands on the right); the others go off along the top and the edges, clear of
// the card's numbers.
const SKY: Sky = [
  [0.84, 0.2, 128, colors.custom_glossYellowHi, 0], [0.56, 0.1, 64, colors.custom_webWhite, 420], [0.97, 0.62, 76, colors.custom_fTeal, 860],
  [0.64, 0.3, 54, colors.custom_glossYellow, 1300], [0.3, 0.04, 56, colors.custom_tabPink, 1750], [0.02, 0.94, 66, colors.custom_gemBlue, 2200],
  [0.45, 0.97, 52, colors.custom_glossYellowHi, 2650],
];
// A firework that may not move is drawn part-open, so the card still has its sky.
const HELD = 0.5;
// Sprinkles that are always on the card, moving or not: [x, y (share of the card), size, colour, a star (1) or a bead (0)].
// They keep to the top and to the cup's side, clear of the card's numbers and its button.
const SPRINKLES: [number, number, number, string, number][] = [
  [0.47, 0.05, 11, colors.custom_webWhite, 1], [0.6, 0.2, 5, colors.custom_glossYellowHi, 0], [0.7, 0.07, 4, colors.custom_fTeal, 0], [0.66, 0.36, 9, colors.custom_glossYellowHi, 1],
  [0.94, 0.06, 10, colors.custom_webWhite, 1], [0.985, 0.34, 5, colors.custom_tabPink, 0], [0.56, 0.44, 4, colors.custom_webWhite, 0], [0.975, 0.93, 9, colors.custom_fTeal, 1],
  [0.012, 0.52, 5, colors.custom_glossYellowHi, 0], [0.35, 0.03, 4, colors.custom_tabPink, 0],
];
const STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z";

function Burst({ x, y, size, color, delay, rest, run }: { x: number; y: number; size: number; color: string; delay: number; rest: number; run: boolean }) {
  const p = useSharedValue(run ? 0 : HELD);
  useEffect(() => {
    if (!run) { p.value = HELD; return; }
    p.value = 0;
    // It bursts, the sky rests (it has faded out by then), and it bursts again; each one rests a little longer than the
    // one before it, so they never go off together twice.
    p.value = withDelay(delay, withRepeat(withSequence(withTiming(1, { duration: 1700, easing: Easing.out(Easing.cubic) }), withTiming(1, { duration: rest }), withTiming(0, { duration: 0 })), -1, false));
    return () => cancelAnimation(p);
  }, [run, delay, rest, p]);
  // Bright while it opens, then it fades as it reaches its full size.
  const style = useAnimatedStyle(() => ({ opacity: p.value < 0.06 ? p.value * 16 : p.value < 0.6 ? 1 : Math.max(0, 1 - (p.value - 0.6) / 0.4), transform: [{ scale: 0.12 + p.value * 0.92 }] }));
  const c = size / 2, thick = size > 90 ? 3.4 : 2.6;
  // Long and short rays in turn, a bright bead at the end of each, and a small ring of beads inside.
  return <Animated.View pointerEvents="none" style={[{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, width: size, height: size, marginLeft: -c, marginTop: -c }, style]}>
    <Svg width={size} height={size}>
      {RAYS.map((a, i) => { const far = i % 2 ? 0.64 : 0.86; return <Line key={a} x1={c + Math.cos(a) * c * 0.24} y1={c + Math.sin(a) * c * 0.24} x2={c + Math.cos(a) * c * far} y2={c + Math.sin(a) * c * far} stroke={color} strokeWidth={i % 2 ? thick - 0.8 : thick} strokeLinecap="round" />; })}
      {RAYS.map((a, i) => <Circle key={`d${a}`} cx={c + Math.cos(a) * c * (i % 2 ? 0.75 : 0.95)} cy={c + Math.sin(a) * c * (i % 2 ? 0.75 : 0.95)} r={i % 2 ? thick * 0.6 : thick * 0.9} fill={i % 2 ? color : colors.custom_webWhite} />)}
      {RAYS.filter((_, i) => i % 2 === 0).map(a => <Circle key={`i${a}`} cx={c + Math.cos(a + 0.22) * c * 0.15} cy={c + Math.sin(a + 0.22) * c * 0.15} r={thick * 0.5} fill={colors.custom_webWhite} />)}
    </Svg>
  </Animated.View>;
}

/**
 * The sky of a Matched card: sprinkles of stars and beads that are always there, and fireworks going off one after
 * another for as long as its screen is in front. Under Reduce Motion, on a covered screen and on a phone that cannot
 * keep up the fireworks stand still, part-open. Goes first inside the card's face, under its words.
 */
export function Fireworks({ testID, sky = SKY }: { testID?: string; sky?: Sky }) {
  const level = useShineLevel();
  const run = !useStill() && level !== STILL && level !== CALM;
  return <View testID={testID} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
    {SPRINKLES.map(([x, y, size, color, star], i) => (star
      ? <Svg key={i} width={size} height={size} viewBox="0 0 24 24" style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, opacity: 0.9 }}><Path d={STAR} fill={color} /></Svg>
      : <View key={i} style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, width: size, height: size, borderRadius: size / 2, backgroundColor: color, opacity: 0.8 }} />))}
    {sky.map(([x, y, size, color, delay], i) => <Burst key={i} x={x} y={y} size={size} color={color} delay={delay} rest={600 + i * 240} run={run} />)}
  </View>;
}

const CUP = require("../../assets/arena/daily_trophy.webp");
/** The golden cup (the All India one, already in the app), floating a little. Its picture is square with the cup in the
 *  middle third, so it is pulled in at the sides: it takes about half of `size` in a row, and all of it in height. */
export function Cup({ size, testID, lift = 0 }: { size: number; testID?: string; lift?: number }) {
  // `lift` = how far it may reach over the rows above and below it, so a tall cup does not make its own row tall.
  return <Alive kind="float" style={{ marginHorizontal: -Math.round(size * 0.24), marginVertical: -lift }}>
    <Image testID={testID} source={CUP} contentFit="contain" accessible={false} style={{ width: size, height: size }} />
  </Alive>;
}

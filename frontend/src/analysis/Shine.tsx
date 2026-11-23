// The shine of the Analysis screen's section pills and report card, of My Tests' tabs and of Home's All India card: a
// running coloured edge, a soft gloss on the upper half and a glass glint that crosses on the diagonal. A face given
// two `tones` also keeps changing them over; a face with its own `backdrop` is never recoloured. Same engine as Rapid Fire's
// glitter ring: CSS animations on the UI thread (plain CSS on the web), moving and fading only, so the screen stays light.
// Under Reduce Motion, or while the screen is covered or hidden, everything rests and the edge is a still coloured slope.
import React, { useMemo, useState } from "react";
import { LayoutChangeEvent, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import Animated, { css } from "react-native-reanimated";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Path } from "react-native-svg";
import { useStill } from "@/src/motion";
import { colors, shineColors } from "@/src/theme";

const TURN = 4200, CYCLE = 3600, TWINKLE = 5200, CHANGE = 5600;
const SPIN = css.keyframes({ from: { transform: [{ rotate: "0deg" }] }, to: { transform: [{ rotate: "360deg" }] } });
// The same two colours the other way round fade in over the face and out again, so they keep changing places.
const SWAP = css.keyframes({ "0%": { opacity: 0 }, "50%": { opacity: 1 }, "100%": { opacity: 0 } });
const STARS = [shineColors[1], shineColors[0], shineColors[3]];
const SPARK = css.keyframes({
  "0%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "0deg" }] },
  "9%": { opacity: 1, transform: [{ scale: 1 }, { rotate: "45deg" }] },
  "18%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "90deg" }] },
  "100%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "90deg" }] },
});
const STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z";
// Where the stars twinkle on the edge (x %, y %), in turn.
const SPOTS: [number, number][] = [[15, 0], [100, 34], [68, 100]];
const tilted = (x: number) => ({ transform: [{ translateX: x }, { rotate: "20deg" }] });

// The glint waits past the left edge, crosses in the first `part` % of the cycle, then waits past the right edge.
// One set of keyframes per rounded distance is kept, so a face keeps the same animation from one draw to the next.
const glints = new Map<string, ReturnType<typeof css.keyframes>>();
function glintPath(w: number, h: number, band: number, part: number) {
  const off = Math.ceil((band + (h + 60) * 0.18) / 10) * 10, to = Math.ceil((w + off) / 60) * 60, key = `${off}:${to}:${part}`;
  let frames = glints.get(key);
  if (!frames) {
    frames = css.keyframes({ "0%": tilted(-off), [`${part}%` as `${number}%`]: tilted(to), "100%": tilted(to) });
    glints.set(key, frames);
  }
  return { hidden: tilted(-off), frames };
}
// A big card's glint: a band that lies across the card from edge to edge, at right angles to the diagonal, and travels
// from just outside one corner to just outside the opposite corner. Sizes are rounded so few keyframe sets are kept.
function cornerPath(w: number, h: number, band: number, part: number) {
  const rw = Math.round(w / 8) * 8, rh = Math.round(h / 8) * 8, key = `c:${rw}:${rh}:${band}:${part}`;
  const diagonal = Math.hypot(rw, rh), reach = diagonal / 2 + band, x = Math.round(rw / diagonal * reach), y = Math.round(rh / diagonal * reach);
  const at = (k: number) => ({ transform: [{ translateX: k * x }, { translateY: k * y }, { rotate: `${Math.round(Math.atan2(rh, rw) * 180 / Math.PI)}deg` }] });
  let frames = glints.get(key);
  if (!frames) {
    frames = css.keyframes({ "0%": at(-1), [`${part}%` as `${number}%`]: at(1), "100%": at(1) });
    glints.set(key, frames);
  }
  const length = Math.ceil(diagonal) + 40;
  return { hidden: at(-1), frames, box: { width: band, height: length, left: (w - band) / 2, top: (h - length) / 2 } };
}

function Sparkles({ count }: { count: number }) {
  return <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={StyleSheet.absoluteFill}>
    {SPOTS.slice(0, count).map(([x, y], i) => <Animated.View key={i} style={[styles.spark, { left: `${x}%`, top: `${y}%` },
      { animationName: SPARK, animationDuration: TWINKLE, animationDelay: 500 + i * (TWINKLE / SPOTS.length), animationIterationCount: "infinite", animationTimingFunction: "ease-out" }]}>
      <Svg width={16} height={16} viewBox="0 0 24 24"><Path d={STAR} fill={STARS[i % STARS.length]} /></Svg>
    </Animated.View>)}
  </View>;
}

/**
 * Wraps a face in the running coloured edge and gives it the gloss and the glint.
 * `tones` = the face's own colours, corner to corner (they change places as time passes); a face that already has its own
 * picture passes it as `backdrop` and is left exactly as it is. `edge` = the colours that run round it (the five by
 * default); `face` = how the face lays out what is inside it; `band` = how wide the glint is; `corner` = the glint goes
 * from one corner to the opposite one (for a big card); `delay` staggers neighbours; `rest` holds everything still.
 */
export function Shine({ children, radius, ring, tones, backdrop, edge = shineColors, gloss, glint, band, part = 40, corner, delay = 0, sparkles = 0, rest, face }: {
  children: React.ReactNode; radius: number; ring: number; tones?: readonly [string, string, ...string[]]; backdrop?: React.ReactNode; edge?: readonly [string, string, ...string[]];
  gloss: string; glint: string; band: number; part?: number; corner?: boolean; delay?: number; sparkles?: number; rest?: boolean; face?: StyleProp<ViewStyle>;
}) {
  const still = useStill() || !!rest;
  const turned = useMemo(() => tones ? [...tones].reverse() as unknown as typeof tones : null, [tones]);
  const [box, setBox] = useState({ w: 0, h: 0 });
  const onLayout = (e: LayoutChangeEvent) => {
    const { width: w, height: h } = e.nativeEvent.layout;
    if (Math.abs(w - box.w) > 1 || Math.abs(h - box.h) > 1) setBox({ w, h });
  };
  const d = Math.ceil(Math.hypot(box.w, box.h)) + 4;
  const path = still || !box.w ? null : corner ? cornerPath(box.w - ring * 2, box.h - ring * 2, band, part) : { ...glintPath(box.w, box.h, band, part), box: { width: band } };
  return <View style={styles.outer}>
    <View onLayout={onLayout} style={[styles.ring, { borderRadius: radius, padding: ring }]}>
      {/* A square as wide as the face's diagonal turns behind it, so the five colours keep running round all four sides. */}
      {box.w ? <Animated.View pointerEvents="none" style={[{ position: "absolute", width: d, height: d, left: (box.w - d) / 2, top: (box.h - d) / 2 },
        still ? null : { animationName: SPIN, animationDuration: TURN, animationDelay: delay, animationIterationCount: "infinite", animationTimingFunction: "linear" }]}>
        <LinearGradient colors={edge} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
      </Animated.View> : <LinearGradient pointerEvents="none" colors={edge} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}
      <View style={[styles.face, { borderRadius: Math.max(0, radius - ring) }, face]}>
        {tones ? <LinearGradient pointerEvents="none" colors={tones} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} /> : backdrop}
        {/* Neighbours start a little apart, so the change travels along a row of pills like a slow wave. */}
        {still || !turned ? null : <Animated.View pointerEvents="none" style={[styles.swap,
          { animationName: SWAP, animationDuration: CHANGE, animationDelay: delay * 3, animationIterationCount: "infinite", animationTimingFunction: "ease-in-out" }]}>
          <LinearGradient colors={turned} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
        </Animated.View>}
        <LinearGradient pointerEvents="none" colors={[gloss, colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.gloss} />
        {path ? <Animated.View pointerEvents="none" style={[corner ? styles.cornerGlint : styles.glint, path.box, path.hidden,
          { animationName: path.frames, animationDuration: CYCLE, animationDelay: delay, animationIterationCount: "infinite", animationTimingFunction: "ease-in-out" }]}>
          <LinearGradient colors={[colors.custom_clear, glint, colors.custom_clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} />
        </Animated.View> : null}
        {children}
      </View>
    </View>
    {still || !sparkles ? null : <Sparkles count={sparkles} />}
  </View>;
}

const styles = StyleSheet.create({
  outer: { position: "relative" },
  ring: { overflow: "hidden", flexGrow: 1 },
  face: { flexGrow: 1, overflow: "hidden" },
  swap: { position: "absolute", left: 0, right: 0, top: 0, bottom: 0, opacity: 0 },
  gloss: { position: "absolute", left: 0, right: 0, top: 0, height: "56%" },
  glint: { position: "absolute", left: 0, top: -30, bottom: -30 },
  cornerGlint: { position: "absolute" },
  spark: { position: "absolute", width: 16, height: 16, marginLeft: -8, marginTop: -8, opacity: 0 },
});

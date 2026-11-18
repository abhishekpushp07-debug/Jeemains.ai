import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Animated, { SharedValue, useAnimatedStyle } from "react-native-reanimated";
import Svg, { Circle, ClipPath, Defs, G, Line, LinearGradient as Grad, Path, RadialGradient, Rect, Stop, Text as SvgText } from "react-native-svg";
import { T } from "@/src/components/ui";
import { arena, cheer, fonts } from "@/src/theme";
import { Crown } from "./parts";

// The stadium banner the cheer squad carries: satin cloth with a glossy top, metallic trim, sporty corner stripes,
// CONGRATULATIONS! in leaning metallic foil, a light glint that crosses it, glitter that keeps catching the light,
// a gold fringe that sways and a halo that pulses on every count. Colours per squad level live in theme `cheer`.
export type CheerLevel = keyof typeof cheer;
const WORD = "CONGRATULATIONS!", WORD_EM = 10.4; // width of the word in Figtree 800, in em
const SLANT = Math.tan((12 * Math.PI) / 180); // the letters lean forward like a team logo
const CUT = 9, PLATE = 26; // corner cut of the cloth, height of the name plate
const STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z";
// Glitter: [x share, y share, size, phase]. Higher squads light more of it.
const GLITTER: [number, number, number, number][] = [
  [0.05, 0.1, 13, 0], [0.95, 0.12, 12, 0.5], [0.22, 0.34, 9, 0.25], [0.79, 0.3, 10, 0.75], [0.5, 0.06, 10, 0.62], [0.36, 0.22, 8, 0.12],
  [0.64, 0.26, 8, 0.37], [0.08, 0.88, 11, 0.85], [0.92, 0.86, 11, 0.3], [0.14, 0.52, 9, 0.68], [0.86, 0.54, 9, 0.18], [0.43, 0.46, 7, 0.55],
  [0.58, 0.44, 7, 0.05], [0.3, 0.62, 7, 0.9], [0.7, 0.64, 7, 0.45], [0.02, 0.5, 10, 0.4], [0.98, 0.46, 10, 0.95], [0.5, 0.98, 9, 0.22],
];
const GLITTER_N: Record<CheerLevel, number> = { 1: 10, 2: 13, 3: 15, 4: 18 };

/** A plate with cut corners, `i` inset from the edge. */
const cut = (w: number, h: number, i = 0) =>
  `M${CUT + i} ${i} H${w - CUT - i} L${w - i} ${CUT + i} V${h - CUT - i} L${w - CUT - i} ${h - i} H${CUT + i} L${i} ${h - CUT - i} V${CUT + i} Z`;

/** Two leaning bars in each lower corner, beside the name plate. */
function stripes(w: number, y0: number, y1: number) {
  const s = (y1 - y0) * SLANT, d: string[] = [];
  for (let k = 0; k < 2; k++) {
    const x = 11 + k * 8, xr = w - 11 - k * 8;
    d.push(`M${x} ${y1} L${x + 4} ${y1} L${x + 4 + s} ${y0} L${x + s} ${y0} Z`, `M${xr - 4 - s} ${y1} L${xr - s} ${y1} L${xr} ${y0} L${xr - 4} ${y0} Z`);
  }
  return d.join(" ");
}

/** One point of glitter that flares now and then. */
function Glitter({ x, y, size, phase, color, t }: { x: number; y: number; size: number; phase: number; color: string; t: SharedValue<number> }) {
  const style = useAnimatedStyle(() => {
    const v = t.value + phase, s = v - Math.floor(v), a = s < 0.42 ? Math.sin((s / 0.42) * Math.PI) : 0;
    return { opacity: a, transform: [{ scale: 0.3 + a * 1.05 }, { rotate: `${s * 120}deg` }] };
  });
  return <Animated.View pointerEvents="none" style={[styles.abs, { left: x - size / 2, top: y - size / 2, width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 24 24"><Path d={STAR} fill={color} /></Svg>
  </Animated.View>;
}

/** The gold fringe under the banner, swaying with the routine. */
function Fringe({ w, top, level, wave }: { w: number; top: number; level: CheerLevel; wave: SharedValue<number> }) {
  const look = cheer[level], step = 5, n = Math.floor((w - 20) / step);
  const sway = useAnimatedStyle(() => ({ transform: [{ skewX: `${Math.sin(wave.value * Math.PI * 2) * 9}deg` }] }));
  return <Animated.View pointerEvents="none" style={[styles.fringe, { top, left: 10, width: w - 20, transformOrigin: "top center" }, sway]}>
    <Svg width={w - 20} height={15}>
      {Array.from({ length: n + 1 }, (_, i) => <Line key={i} x1={i * step + 1} y1={0} x2={i * step + 1} y2={i % 2 ? 11 : 13} stroke={look.trim[i % 3 === 0 ? 0 : 1]} strokeWidth={1.6} strokeLinecap="round" />)}
      <Line x1={0} y1={1} x2={w - 20} y2={1} stroke={look.trim[2]} strokeWidth={2} />
    </Svg>
  </Animated.View>;
}

/** A gold pole with a spear tip; the holder grips it at the bottom. */
export function Pole({ height, level, side }: { height: number; level: CheerLevel; side: "left" | "right" }) {
  const t = cheer[level].trim;
  return <View pointerEvents="none" style={[styles.pole, side === "left" ? styles.poleL : styles.poleR, { height: height + 16 }]}>
    <View style={[styles.rod, { height }]}><LinearGradient colors={[t[2], t[0], t[1], t[2]]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} /></View>
    <Svg width={16} height={22} viewBox="0 0 16 22" style={styles.tip}><Path d="M8 0 L14 13 L8 22 L2 13 Z" fill={t[0]} stroke={t[2]} strokeWidth={1.3} strokeLinejoin="round" /><Path d="M8 3 L11 13 L8 18 Z" fill={t[1]} /></Svg>
  </View>;
}

/** The banner itself. `top` keeps the title clear of the champion's medal that hangs over the top edge.
 *  `word`: the foil title (CONGRATULATIONS! by default); without `crown` the name plate shows the name only. */
export function CheerBanner({ w, h, top, level, name, crown, word = WORD, clock, count, glitter, wave, sweep }: {
  w: number; h: number; top: number; level: CheerLevel; name: string; crown?: { won: number; real: number }; word?: string;
  clock: SharedValue<number>; count: number; glitter: SharedValue<number>; wave: SharedValue<number>; sweep: SharedValue<number>;
}) {
  const look = cheer[level], L = level;
  const fs = Math.min(h * 0.3, (w - 36) / ((WORD_EM * word.length) / WORD.length)), cap = fs * 0.7, yb = top + 5 + cap + 4, xm = w / 2 + SLANT * (yb - cap / 2);
  // Narrow banners drop the corner stripes so the champion's name always fits on the plate.
  const plateTop = h - 8 - PLATE, striped = w >= 210, side = striped ? 11 + 2 * 8 + (h - 7 - plateTop) * SLANT + 4 : 10;
  const halo = useAnimatedStyle(() => { const x = clock.value * count, k = x - Math.floor(x); return { opacity: 0.45 + (1 - Math.min(1, k * 3)) * 0.55 }; });
  const punch = useAnimatedStyle(() => { const x = clock.value * count, k = x - Math.floor(x); return { transform: [{ scale: 1 + (1 - Math.min(1, k * 5)) * 0.045 }] }; });
  const glint = useAnimatedStyle(() => ({ transform: [{ translateX: -80 + sweep.value * (w + 160) }, { rotate: "18deg" }] }));
  return <View testID="cheer-banner" style={{ width: w, height: h }}>
    <Animated.View pointerEvents="none" style={[styles.abs, { left: -w * 0.2, top: -h * 0.55, width: w * 1.4, height: h * 2.1 }, halo]}>
      <Svg width={w * 1.4} height={h * 2.1}>
        <Defs><RadialGradient id={`halo${L}`} cx="50%" cy="50%" rx="50%" ry="50%"><Stop offset="0" stopColor={look.trim[1]} stopOpacity={0.6} /><Stop offset="0.55" stopColor={look.trim[1]} stopOpacity={0.18} /><Stop offset="1" stopColor={look.trim[1]} stopOpacity={0} /></RadialGradient></Defs>
        <Rect width={w * 1.4} height={h * 2.1} fill={`url(#halo${L})`} />
      </Svg>
    </Animated.View>
    <Fringe w={w} top={h - 3} level={level} wave={wave} />
    <View style={[styles.cloth, { width: w, height: h }]}>
      <Svg width={w} height={h}>
        <Defs>
          <ClipPath id={`clip${L}`}><Path d={cut(w, h)} /></ClipPath>
          <Grad id={`cloth${L}`} x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={look.cloth[0]} /><Stop offset="0.55" stopColor={look.cloth[1]} /><Stop offset="1" stopColor={look.cloth[2]} /></Grad>
          <Grad id={`gloss${L}`} x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={arena.text} stopOpacity={0.32} /><Stop offset="1" stopColor={arena.text} stopOpacity={0} /></Grad>
          <Grad id={`satin${L}`} x1="0" y1="0" x2="1" y2="0"><Stop offset="0" stopColor={arena.text} stopOpacity={0} /><Stop offset="0.5" stopColor={arena.text} stopOpacity={0.1} /><Stop offset="1" stopColor={arena.text} stopOpacity={0} /></Grad>
          <Grad id={`trim${L}`} x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={look.trim[0]} /><Stop offset="0.5" stopColor={look.trim[1]} /><Stop offset="1" stopColor={look.trim[2]} /></Grad>
        </Defs>
        <G clipPath={`url(#clip${L})`}>
          <Rect width={w} height={h} fill={`url(#cloth${L})`} />
          <Rect x={w * 0.16} width={w * 0.24} height={h} fill={`url(#satin${L})`} />
          <Rect x={w * 0.6} width={w * 0.22} height={h} fill={`url(#satin${L})`} />
          <Rect width={w} height={h * 0.46} fill={`url(#gloss${L})`} />
          {striped ? <Path d={stripes(w, plateTop - 2, h - 7)} fill={look.stripe} fillOpacity={0.9} /> : null}
        </G>
        <Path d={cut(w, h, 5)} fill="none" stroke={look.trim[0]} strokeOpacity={0.55} strokeWidth={1} />
        <Path d={cut(w, h, 1.5)} fill="none" stroke={`url(#trim${L})`} strokeWidth={3} />
        {[14, w - 14].map((x) => <Circle key={x} cx={x} cy={10} r={3.2} fill={look.ink} stroke={look.trim[0]} strokeWidth={1.4} />)}
      </Svg>
      <Animated.View pointerEvents="none" style={[styles.glint, { height: h * 2.4, top: -h * 0.7 }, glint]}>
        <LinearGradient colors={[arena.clear, arena.gloss, arena.glint, arena.gloss, arena.clear]} locations={[0, 0.4, 0.5, 0.6, 1]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} />
      </Animated.View>
    </View>
    <Animated.View testID="cheer-banner-title" style={[StyleSheet.absoluteFill, punch]} pointerEvents="none" accessible accessibilityLabel={word}>
      <Svg width={w} height={h}>
        <Defs><Grad id={`foil${L}`} x1="0" y1={yb - cap} x2="0" y2={yb} gradientUnits="userSpaceOnUse">{look.foil.map((c, i) => <Stop key={i} offset={i / (look.foil.length - 1)} stopColor={c} />)}</Grad></Defs>
        <G transform="skewX(-12)">
          <SvgText x={xm + SLANT * 2.5} y={yb + 2.5} fill={look.ink} fillOpacity={0.85} fontSize={fs} fontFamily={fonts.heavy} textAnchor="middle">{word}</SvgText>
          <SvgText x={xm} y={yb} fill={look.ink} stroke={look.ink} strokeWidth={3} strokeLinejoin="round" fontSize={fs} fontFamily={fonts.heavy} textAnchor="middle">{word}</SvgText>
          <SvgText x={xm} y={yb} fill={`url(#foil${L})`} fontSize={fs} fontFamily={fonts.heavy} textAnchor="middle">{word}</SvgText>
        </G>
      </Svg>
    </Animated.View>
    <View pointerEvents="none" style={[styles.plateRow, { top: plateTop, paddingHorizontal: side }]}>
      <View style={[styles.plate, { backgroundColor: look.plate, borderColor: look.trim[1] }]}>
        <T testID="cheer-banner-name" w="heavy" size={Math.min(16, w / 15)} color={arena.text} numberOfLines={1} style={styles.shrink}>{name}</T>
        {crown ? <Crown c={crown} /> : null}
      </View>
    </View>
    {GLITTER.slice(0, GLITTER_N[level]).map(([x, y, size, phase], i) => <Glitter key={i} x={x * w} y={y * h} size={size * 1.35} phase={phase} color={look.glitter[i % look.glitter.length]} t={glitter} />)}
  </View>;
}

const styles = StyleSheet.create({
  abs: { position: "absolute" }, shrink: { flexShrink: 1 },
  cloth: { borderRadius: CUT * 0.6, overflow: "hidden" },
  glint: { position: "absolute", left: 0, width: 46 },
  fringe: { position: "absolute", height: 15 },
  plateRow: { position: "absolute", left: 0, right: 0, alignItems: "center" },
  plate: { maxWidth: "100%", height: PLATE, paddingHorizontal: 10, borderRadius: PLATE / 2, borderWidth: 1.5, flexDirection: "row", alignItems: "center", gap: 6 },
  pole: { position: "absolute", top: -28, width: 16, alignItems: "center" }, poleL: { left: -4 }, poleR: { right: -4 },
  rod: { position: "absolute", top: 16, width: 7, borderRadius: 3.5, overflow: "hidden" },
  tip: { position: "absolute", top: 0 },
});

import React, { useState } from "react";
import { LayoutChangeEvent, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import Animated, { css } from "react-native-reanimated";
import { useStill } from "@/src/motion";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Path } from "react-native-svg";
import { arena, fx, glitterColors } from "@/src/theme";

// The glittering border of every Rapid Fire card: a ring of colours running round the edge, with little stars that
// sparkle here and there. CSS animations run on the UI thread (and as plain CSS on the web), so many cards stay smooth.

const SPIN = css.keyframes({ from: { transform: [{ rotate: "0deg" }] }, to: { transform: [{ rotate: "360deg" }] } });
const SPARK = css.keyframes({
  "0%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "0deg" }] },
  "9%": { opacity: 1, transform: [{ scale: 1 }, { rotate: "45deg" }] },
  "18%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "90deg" }] },
  "100%": { opacity: 0, transform: [{ scale: 0.2 }, { rotate: "90deg" }] },
});
const STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z";
// Where the stars sparkle on the edge (x %, y %), in turn.
const SPOTS: [number, number][] = [[18, 0], [100, 38], [64, 100], [0, 70]];
const CYCLE = 5200;

// Size, place and flex settings belong to the outside of the ring; everything else (padding, layout, colour) to the inside.
const OUTER = new Set(["margin", "marginTop", "marginBottom", "marginLeft", "marginRight", "marginHorizontal", "marginVertical", "flex", "flexGrow", "flexShrink", "flexBasis",
  "alignSelf", "width", "minWidth", "maxWidth", "position", "top", "left", "right", "bottom", "zIndex", "opacity", "transform", "aspectRatio"]);
export function splitStyle(style: StyleProp<ViewStyle>): [ViewStyle, ViewStyle] {
  const out: Record<string, unknown> = {}, inn: Record<string, unknown> = {};
  Object.entries(StyleSheet.flatten(style) || {}).forEach(([k, v]) => { (OUTER.has(k) ? out : inn)[k] = v; });
  return [out as ViewStyle, inn as ViewStyle];
}

function Sparkles({ count }: { count: number }) {
  return <View pointerEvents="none" style={StyleSheet.absoluteFill}>
    {SPOTS.slice(0, count).map(([x, y], i) => <Animated.View key={i} style={[styles.spark, { left: `${x}%`, top: `${y}%` },
      { animationName: SPARK, animationDuration: CYCLE, animationDelay: i * (CYCLE / SPOTS.length) + (x % 7) * 90, animationIterationCount: "infinite", animationTimingFunction: "ease-out" }]}>
      <Svg width={14} height={14} viewBox="0 0 24 24"><Path d={STAR} fill={i % 2 ? fx.white : arena.gold} /></Svg>
    </Animated.View>)}
  </View>;
}

/**
 * Wraps a card in the running glitter ring. `inner` is the card's own face (its background must be solid: the ring is
 * the colour that shows round it). `sparkles` = how many stars twinkle on the edge (0 for long lists).
 */
export function Glitter({ children, radius = 20, ring = 2, style, inner, sparkles = 3, testID, pointerEvents }: {
  children: React.ReactNode; radius?: number; ring?: number; style?: StyleProp<ViewStyle>; inner?: StyleProp<ViewStyle>; sparkles?: number; testID?: string;
  pointerEvents?: "box-none" | "none" | "auto" | "box-only";
}) {
  const reduced = useStill();
  const [box, setBox] = useState({ w: 0, h: 0 });
  const onLayout = (e: LayoutChangeEvent) => {
    const { width: w, height: h } = e.nativeEvent.layout;
    if (Math.abs(w - box.w) > 1 || Math.abs(h - box.h) > 1) setBox({ w, h });
  };
  const d = Math.ceil(Math.hypot(box.w, box.h)) + 4;
  return <View testID={testID} pointerEvents={pointerEvents} style={[styles.outer, { borderRadius: radius }, style]}>
    <View onLayout={onLayout} style={[styles.ring, { borderRadius: radius, padding: ring }]}>
      {/* A square as wide as the card's diagonal turns behind it, so the colours keep running round all four sides. */}
      {box.w ? <Animated.View pointerEvents="none" style={[{ position: "absolute", width: d, height: d, left: (box.w - d) / 2, top: (box.h - d) / 2 },
        reduced ? null : { animationName: SPIN, animationDuration: 4200, animationIterationCount: "infinite", animationTimingFunction: "linear" }]}>
        <LinearGradient colors={glitterColors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
      </Animated.View> : <LinearGradient pointerEvents="none" colors={glitterColors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}
      <View style={[styles.inner, { borderRadius: Math.max(0, radius - ring) }, inner]}>{children}</View>
    </View>
    {reduced || !sparkles ? null : <Sparkles count={sparkles} />}
  </View>;
}

const styles = StyleSheet.create({
  outer: { position: "relative" },
  ring: { overflow: "hidden", flexGrow: 1 },
  inner: { flexGrow: 1, overflow: "hidden", backgroundColor: arena.panel },
  spark: { position: "absolute", width: 14, height: 14, marginLeft: -7, marginTop: -7, opacity: 0 },
});

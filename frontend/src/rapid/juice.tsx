import React, { useEffect, useState } from "react";
import { Pressable, PressableProps, StyleProp, StyleSheet, View, ViewStyle, useWindowDimensions } from "react-native";
import Animated, { Easing, ZoomIn, cancelAnimation, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withSpring, withTiming } from "react-native-reanimated";
import Svg, { Path } from "react-native-svg";
import { T, tap } from "@/src/components/ui";
import { arena, fx } from "@/src/theme";
import { useLowMotion, useStill } from "@/src/motion";

// The playful layer of the arena: squashy presses, twinkles, confetti and counting numbers.
// Everything here is transform/opacity only and goes still when Reduce Motion is on; confetti, counting and pop-ins
// also rest on a phone that cannot move anything smoothly (useLowMotion).

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);
/** A fixed pseudo-random number in [0, 1) for piece i, property k: the same layout on every render. */
export const rnd = (i: number, k: number) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };

/** Squashy press: flattens under the thumb, then springs back with a wobble. */
export function Jelly({ children, onPress, onLongPress, style, testID, disabled, accessibilityLabel, accessibilityState, accessibilityRole = "button", hitSlop }: {
  children: React.ReactNode; onPress?: () => void; onLongPress?: () => void; style?: StyleProp<ViewStyle>; testID?: string; disabled?: boolean; accessibilityLabel?: string;
  accessibilityState?: PressableProps["accessibilityState"]; accessibilityRole?: PressableProps["accessibilityRole"]; hitSlop?: PressableProps["hitSlop"];
}) {
  const reduced = useReducedMotion();
  const s = useSharedValue(0);
  const a = useAnimatedStyle(() => ({ transform: [{ scaleX: 1 + s.value * 0.06 }, { scaleY: 1 - s.value * 0.09 }] }));
  return <AnimatedPressable testID={testID} disabled={disabled} hitSlop={hitSlop} accessibilityRole={accessibilityRole} accessibilityLabel={accessibilityLabel}
    accessibilityState={{ ...accessibilityState, disabled: !!disabled }} aria-selected={accessibilityState?.selected}
    onPressIn={() => { if (!reduced) s.value = withTiming(1, { duration: 70 }); }}
    onPressOut={() => { s.value = reduced ? 0 : withSpring(0, { damping: 5, stiffness: 300, mass: 0.6 }); }}
    onLongPress={onLongPress ? () => { tap(); onLongPress(); } : undefined}
    onPress={() => { tap(); onPress?.(); }} style={[style, a, disabled && styles.off]}>{children}</AnimatedPressable>;
}

const STAR = "M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z";
function Twinkle({ x, y, size, i, color }: { x: number; y: number; size: number; i: number; color: string }) {
  const t = useSharedValue(0);
  useEffect(() => {
    t.value = withDelay(i * 420, withRepeat(withSequence(withTiming(1, { duration: 520, easing: Easing.out(Easing.quad) }), withTiming(0, { duration: 620 }), withDelay(900 + (i % 3) * 500, withTiming(0, { duration: 0 }))), -1, false));
    return () => cancelAnimation(t);
  }, [t, i]);
  const a = useAnimatedStyle(() => ({ opacity: t.value, transform: [{ scale: 0.3 + 0.7 * t.value }, { rotate: `${t.value * 45}deg` }] }));
  return <Animated.View style={[styles.abs, { left: `${x}%`, top: `${y}%`, width: size, height: size, marginLeft: -size / 2, marginTop: -size / 2 }, a]}>
    <Svg width={size} height={size} viewBox="0 0 24 24"><Path d={STAR} fill={color} /></Svg>
  </Animated.View>;
}
/** Little stars that blink around a piece of artwork. `spots` are [x %, y %, size]. */
export function Twinkles({ spots, color = arena.gold }: { spots: [number, number, number][]; color?: string }) {
  const reduced = useStill();
  if (reduced) return null;
  return <View pointerEvents="none" style={StyleSheet.absoluteFill}>{spots.map(([x, y, size], i) => <Twinkle key={i} i={i} x={x} y={y} size={size} color={i % 3 === 2 ? fx.white : color} />)}</View>;
}

const CONFETTI = [arena.gold, arena.tealHi, fx.crimson, fx.white, arena.aqua, fx.ember];
function Piece({ i, w, h, colors }: { i: number; w: number; h: number; colors: readonly string[] }) {
  const t = useSharedValue(0);
  const x0 = rnd(i, 1) * w, drift = (rnd(i, 2) - 0.5) * 140, size = 7 + rnd(i, 4) * 7;
  useEffect(() => { t.value = withDelay(rnd(i, 5) * 400, withTiming(1, { duration: 1500 + rnd(i, 3) * 1400, easing: Easing.in(Easing.quad) })); }, [t, i]);
  const a = useAnimatedStyle(() => ({ opacity: interpolate(t.value, [0, 0.85, 1], [1, 1, 0]), transform: [{ translateX: x0 + drift * t.value }, { translateY: -24 + t.value * h * 0.85 }, { rotate: `${t.value * (500 + i * 40)}deg` }] }));
  return <Animated.View style={[styles.abs, { width: size, height: size * 0.55, borderRadius: 2, backgroundColor: colors[i % colors.length] }, a]} />;
}
/** One shower of confetti for a win. Never loops. */
export function Confetti({ count = 30, colors = CONFETTI }: { count?: number; colors?: readonly string[] }) {
  const reduced = useLowMotion();
  const { width, height } = useWindowDimensions();
  if (reduced) return null;
  return <View pointerEvents="none" testID="rf-confetti" style={[StyleSheet.absoluteFill, styles.top]}>{Array.from({ length: count }, (_, i) => <Piece key={i} i={i} w={width} h={height} colors={colors} />)}</View>;
}

/** A number that counts up to its value. */
export function Count({ to, prefix = "", size = 24, color = arena.text, testID }: { to: number; prefix?: string; size?: number; color?: string; testID?: string }) {
  const reduced = useLowMotion();
  const [v, setV] = useState(reduced ? to : 0);
  useEffect(() => {
    if (reduced) { setV(to); return; }
    let k = 0;
    const iv = setInterval(() => { k += 1; setV(Math.round((to * k) / 18)); if (k >= 18) clearInterval(iv); }, 35);
    return () => clearInterval(iv);
  }, [to, reduced]);
  return <T testID={testID} w="heavy" size={size} color={color}>{prefix}{v}</T>;
}

/** Children pop in once, smoothly (no springy wobble: a wobble read as the cards flickering), one after another when given a delay. */
export function Pop({ children, delay = 0, style }: { children: React.ReactNode; delay?: number; style?: StyleProp<ViewStyle> }) {
  const reduced = useLowMotion();
  return <Animated.View entering={reduced ? undefined : ZoomIn.delay(delay).duration(220).easing(Easing.out(Easing.cubic))} style={style}>{children}</Animated.View>;
}

function Wave({ i, size }: { i: number; size: number }) {
  const t = useSharedValue(0);
  useEffect(() => {
    t.value = withDelay(i * 600, withRepeat(withTiming(1, { duration: 1800, easing: Easing.out(Easing.quad) }), -1, false));
    return () => cancelAnimation(t);
  }, [t, i]);
  const a = useAnimatedStyle(() => ({ opacity: 0.7 * (1 - t.value), transform: [{ scale: 0.35 + t.value * 0.75 }] }));
  return <Animated.View style={[styles.abs, { width: size, height: size, borderRadius: size / 2, borderWidth: 3, borderColor: arena.tealHi }, a]} />;
}
/** Radar rings spreading out from whatever sits in the middle (searching for a rival). */
export function Radar({ size = 240, children }: { size?: number; children: React.ReactNode }) {
  const reduced = useStill();
  return <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
    {reduced ? <View style={[styles.abs, { width: size * 0.8, height: size * 0.8, borderRadius: size, borderWidth: 3, borderColor: arena.tealDeep }]} /> : [0, 1, 2].map((i) => <Wave key={i} i={i} size={size} />)}
    {children}
  </View>;
}

/** A red "live" dot that pulses (still under Reduce Motion). */
export function LiveDot({ size = 10, color = fx.crimson }: { size?: number; color?: string }) {
  const reduced = useStill();
  const t = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    t.value = 0;
    t.value = withRepeat(withTiming(1, { duration: 1100, easing: Easing.out(Easing.quad) }), -1, false);
    return () => cancelAnimation(t);
  }, [t, reduced]);
  const ring = useAnimatedStyle(() => ({ opacity: 0.8 * (1 - t.value), transform: [{ scale: 1 + t.value * 1.4 }] }));
  return <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
    {reduced ? null : <Animated.View style={[styles.abs, { width: size, height: size, borderRadius: size, backgroundColor: color }, ring]} />}
    <View style={{ width: size, height: size, borderRadius: size, backgroundColor: color }} />
  </View>;
}

const styles = StyleSheet.create({ off: { opacity: 0.5 }, abs: { position: "absolute" }, top: { zIndex: 60 } });

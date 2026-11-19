import React, { useEffect, useId, useMemo } from "react";
import { ActivityIndicator, Pressable, StyleProp, StyleSheet, View, ViewStyle, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle, Defs, Ellipse, G, Path, RadialGradient, Rect, Stop, Text as SvgText } from "react-native-svg";
import Animated, { Easing, cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Icon, IconName, T, tap } from "@/src/components/ui";
import { arena, fonts } from "@/src/theme";
import { GameIcon, GameIconName } from "./Art";
import { Glitter, splitStyle } from "./Glitter";

// Blood Red Arena building blocks. Shining blood red is the stage, teal is anything you press, gold is for wins and rewards.

const MARKS: { k: "gem" | "bolt" | "atom" | "txt"; x: number; y: number; s: number; r: number; t?: string }[] = [
  { k: "gem", x: 0.14, y: 0.1, s: 92, r: -14 }, { k: "txt", x: 0.78, y: 0.16, s: 120, r: 10, t: "∑" }, { k: "atom", x: 0.84, y: 0.36, s: 110, r: 20 },
  { k: "bolt", x: 0.1, y: 0.4, s: 110, r: 12 }, { k: "txt", x: 0.5, y: 0.52, s: 130, r: -8, t: "π" }, { k: "gem", x: 0.86, y: 0.66, s: 110, r: 18 },
  { k: "txt", x: 0.14, y: 0.72, s: 120, r: -12, t: "∫" }, { k: "atom", x: 0.3, y: 0.9, s: 100, r: -20 }, { k: "bolt", x: 0.72, y: 0.9, s: 96, r: -10 }, { k: "txt", x: 0.5, y: 0.24, s: 84, r: 6, t: "λ" },
];
const Marks = React.memo(function Marks({ w, h, dim }: { w: number; h: number; dim?: boolean }) {
  return <Svg pointerEvents="none" width={w} height={h} style={StyleSheet.absoluteFill} opacity={dim ? 0.22 : 0.5}>
    {MARKS.map((m, i) => {
      const s = m.s / 100;
      return <G key={i} transform={`translate(${m.x * w} ${m.y * h}) rotate(${m.r}) scale(${s})`}>
        {m.k === "gem" ? <Path d="M-34 -18 L-18 -40 L18 -40 L34 -18 L0 42 Z M-34 -18 L34 -18 M-18 -40 L-8 -18 L0 42 L8 -18 L18 -40" stroke={arena.mark} strokeWidth={5} strokeLinejoin="round" fill="none" />
          : m.k === "bolt" ? <Path d="M10 -46 L-26 6 L-4 6 L-14 46 L26 -8 L4 -8 Z" fill={arena.mark} />
          : m.k === "atom" ? <G stroke={arena.mark} strokeWidth={5} fill="none"><Ellipse rx={44} ry={16} /><Ellipse rx={44} ry={16} transform="rotate(60)" /><Ellipse rx={44} ry={16} transform="rotate(120)" /><Circle r={6} fill={arena.mark} /></G>
          : <SvgText fill={arena.mark} fontSize={90} fontWeight="800" textAnchor="middle" y={30}>{m.t}</SvgText>}
      </G>;
    })}
  </Svg>;
});

/** A slow band of light that crosses the stage every few seconds, like light sliding over polished red glass. */
function Shine({ w, h }: { w: number; h: number }) {
  const reduced = useReducedMotion();
  const x = useSharedValue(0);
  useEffect(() => {
    if (reduced) return;
    x.value = withDelay(900, withRepeat(withSequence(withTiming(1, { duration: 2600, easing: Easing.inOut(Easing.quad) }), withDelay(5200, withTiming(0, { duration: 0 }))), -1, false));
    return () => cancelAnimation(x);
  }, [reduced, x]);
  const band = Math.min(w, 560) * 0.5;
  // The band is tilted, so it starts and ends well outside the screen.
  const a = useAnimatedStyle(() => ({ transform: [{ translateX: -(band + h * 0.5) + x.value * (w + band + h) }, { rotate: "18deg" }] }));
  if (reduced) return null;
  return <Animated.View pointerEvents="none" style={[{ position: "absolute", left: 0, top: -h * 0.2, width: band, height: h * 1.4 }, a]}>
    <LinearGradient colors={[arena.clear, arena.shine, arena.clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} />
  </Animated.View>;
}

/** Shining blood-red stage: a hot glow at the top, big faint marks, darker edges and a slow band of light. `dim` quietens it all behind a question. */
export function ArenaBg({ children, dim, style, testID }: { children: React.ReactNode; dim?: boolean; style?: StyleProp<ViewStyle>; testID?: string }) {
  const { width, height } = useWindowDimensions();
  const id = "arenaEdge" + useId().replace(/[^a-zA-Z0-9]/g, "");
  return <View testID={testID} style={[styles.bg, style]}>
    <LinearGradient pointerEvents="none" colors={[arena.bgTop, arena.bg, arena.bgDeep]} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFill} />
    <Marks w={width} h={height} dim={dim} />
    {/* Explicit stopOpacity: native SVG ignores alpha inside stopColor. */}
    <Svg pointerEvents="none" width={width} height={height} style={StyleSheet.absoluteFill}>
      <Defs>
        <RadialGradient id={id} cx="50%" cy="42%" rx="75%" ry="62%"><Stop offset="0.55" stopColor={arena.vignette} stopOpacity={0} /><Stop offset="1" stopColor={arena.vignette} stopOpacity={0.62} /></RadialGradient>
        <RadialGradient id={`${id}Glow`} cx="50%" cy="0%" rx="90%" ry="44%"><Stop offset="0" stopColor={arena.glow} stopOpacity={dim ? 0.2 : 0.5} /><Stop offset="1" stopColor={arena.glow} stopOpacity={0} /></RadialGradient>
      </Defs>
      <Rect x={0} y={0} width={width} height={height} fill={`url(#${id}Glow)`} />
      <Rect x={0} y={0} width={width} height={height} fill={`url(#${id})`} />
    </Svg>
    {dim ? null : <Shine w={width} h={height} />}
    {children}
  </View>;
}

/** Raised black-cherry glass panel with a glossy top and the running glitter border. `gold` keeps the golden lip for rewards and showcases. */
export function Panel({ children, style, testID, gold, flat, sparkles }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; testID?: string; gold?: boolean; flat?: boolean; sparkles?: number }) {
  const [outer, { borderRadius, ...inner }] = splitStyle(style);
  return <Glitter testID={testID} radius={typeof borderRadius === "number" ? borderRadius : 20} sparkles={sparkles ?? (flat ? 1 : 3)} style={[!flat && styles.panelLift, outer]}
    inner={[styles.panel, gold && styles.panelGold, flat && styles.panelFlat, inner]}>
    <LinearGradient pointerEvents="none" colors={[arena.panelGloss, arena.clear]} style={styles.panelSheen} />
    <LinearGradient pointerEvents="none" colors={[arena.clear, gold ? arena.gold : arena.rimHi, arena.clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.hairline} />
    {children}
  </Glitter>;
}

type Tone = "teal" | "wine" | "danger";
const TONES: Record<Tone, { hi: string; face: string; lip: string; line: string; ink: string }> = {
  teal: { hi: arena.tealHi, face: arena.teal, lip: arena.tealDeep, line: arena.tealOutline, ink: arena.text },
  wine: { hi: arena.rim, face: arena.panelHi, lip: arena.panelEdge, line: arena.rim, ink: arena.text },
  danger: { hi: arena.panelHi, face: arena.panel, lip: arena.panelEdge, line: arena.danger, ink: arena.danger },
};

/** Thick raised button: glossy top, dark lower edge, and it sinks when pressed. `streak` runs a slow line of light across it. */
export function RaisedButton({ label, sub, icon, glyph, onPress, disabled, busy, testID, height = 52, tone = "teal", streak, style, accessibilityLabel, children }: {
  label?: string; sub?: string; icon?: GameIconName; glyph?: IconName; onPress?: () => void; disabled?: boolean; busy?: boolean; testID?: string; height?: number; tone?: Tone;
  streak?: boolean; style?: StyleProp<ViewStyle>; accessibilityLabel?: string; children?: React.ReactNode;
}) {
  const reduced = useReducedMotion();
  const c = TONES[tone], lip = height >= 60 ? 7 : 5, radius = Math.min(22, height / 2.6);
  const down = useSharedValue(0), x = useSharedValue(0);
  const off = disabled || busy;
  useEffect(() => {
    if (!streak || reduced || off) return;
    x.value = withRepeat(withSequence(withTiming(1, { duration: 1300, easing: Easing.inOut(Easing.quad) }), withDelay(1900, withTiming(0, { duration: 0 }))), -1, false);
  }, [streak, reduced, off, x]);
  const face = useAnimatedStyle(() => ({ transform: [{ translateY: down.value * (lip - 1) }] }));
  const light = useAnimatedStyle(() => ({ transform: [{ translateX: -120 + x.value * 560 }, { rotate: "18deg" }] }));
  const big = height >= 60, narrow = useWindowDimensions().width < 360; // small phones: a slightly smaller label so it never cuts off
  return <Pressable testID={testID} disabled={off} accessibilityRole="button" accessibilityLabel={accessibilityLabel || (sub ? `${label}, ${sub}` : label)} accessibilityState={{ disabled: !!off, busy: !!busy }}
    onPressIn={() => { down.value = withTiming(1, { duration: 70 }); }} onPressOut={() => { down.value = withTiming(0, { duration: 130 }); }} onPress={() => { tap(); onPress?.(); }}
    style={[{ height: height + lip, borderRadius: radius, backgroundColor: c.lip, opacity: disabled ? 0.5 : 1 }, style]}>
    <Animated.View style={[{ height, borderRadius: radius, overflow: "hidden", borderWidth: 1.5, borderColor: c.line }, face]}>
      <LinearGradient colors={[c.hi, c.face]} style={StyleSheet.absoluteFill} />
      <View pointerEvents="none" style={[styles.gloss, { borderRadius: radius }]} />
      {streak ? <Animated.View pointerEvents="none" style={[styles.streak, light]}><LinearGradient colors={[arena.clear, arena.sheen, arena.clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} /></Animated.View> : null}
      <View style={styles.buttonRow}>
        {busy ? <ActivityIndicator color={c.ink} /> : icon ? <GameIcon name={icon} size={big ? 44 : 30} /> : glyph ? <Icon name={glyph} size={big ? 24 : 20} color={c.ink} /> : null}
        {children || <View style={styles.buttonCopy}>
          <T w="heavy" size={big ? (narrow ? 19 : 24) : height >= 50 && !narrow ? 16 : 14} color={c.ink} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.75} style={[styles.inkShadow, { textShadowColor: tone === "teal" ? arena.tealOutline : arena.panelEdge, letterSpacing: big ? (narrow ? 1 : 2) : 0.3 }]}>{label}</T>
          {sub ? <T w="bold" size={11} color={c.ink} numberOfLines={1} style={{ opacity: 0.9 }}>{sub}</T> : null}
        </View>}
      </View>
    </Animated.View>
  </Pressable>;
}

export function BackButton({ onPress, testID = "rf-back", label = "Back" }: { onPress: () => void; testID?: string; label?: string }) {
  return <RaisedButton testID={testID} accessibilityLabel={label} onPress={onPress} height={42} style={styles.back}><GameIcon name="back" size={30} /></RaisedButton>;
}
export function CloseButton({ onPress, testID, label = "Close" }: { onPress: () => void; testID?: string; label?: string }) {
  return <RaisedButton testID={testID} accessibilityLabel={label} onPress={onPress} height={42} tone="wine" style={styles.back}><Icon name="close" size={22} color={arena.text} /></RaisedButton>;
}

/** Bright yellow count, readable on crimson. */
export function Badge({ n, testID, style }: { n: number | string; testID?: string; style?: StyleProp<ViewStyle> }) {
  return <View testID={testID} style={[styles.badge, style]}><T w="heavy" size={11} color={arena.badgeInk}>{n}</T></View>;
}
export function OnlineDot({ size = 12 }: { size?: number }) {
  return <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: arena.online, borderWidth: 2, borderColor: arena.panelEdge }} />;
}

/** Golden heading with a dark outline. */
export function GoldTitle({ children, size = 22, testID, center, lines }: { children: React.ReactNode; size?: number; testID?: string; center?: boolean; lines?: number }) {
  return <T testID={testID} w="heavy" size={size} color={arena.gold} numberOfLines={lines} adjustsFontSizeToFit={!!lines} minimumFontScale={0.8} style={[styles.goldShadow, center && styles.center, { letterSpacing: size > 26 ? 1.5 : 0.3 }]}>{children}</T>;
}
export function ScreenTop({ title, sub, onBack, right, testID }: { title: string; sub?: string; onBack: () => void; right?: React.ReactNode; testID?: string }) {
  return <View style={styles.top}>
    <BackButton onPress={onBack} testID={testID ? `${testID}-back` : "rf-back"} />
    <View style={styles.flex}><GoldTitle testID={testID ? `${testID}-title` : undefined}>{title}</GoldTitle>{sub ? <T w="bold" size={12} color={arena.aqua} numberOfLines={1}>{sub}</T> : null}</View>
    {right}
  </View>;
}
export function SectionTitle({ title, action, onAction, testID }: { title: string; action?: string; onAction?: () => void; testID?: string }) {
  return <View style={styles.section}>
    <GoldTitle size={17}>{title}</GoldTitle>
    {action ? <Pressable testID={testID} onPress={onAction} accessibilityRole="button" accessibilityLabel={action} style={styles.sectionAction}><T w="heavy" size={13} color={arena.aqua}>{action}</T></Pressable> : null}
  </View>;
}

/** Tabs inside a screen, framed by the glitter border. The chosen one is a pressed-in teal key. */
export function Segment<K extends string>({ items, value, onChange, prefix }: { items: [K, string][]; value: K; onChange: (k: K) => void; prefix: string }) {
  return <Glitter radius={16} sparkles={2} inner={styles.segment}>
    {items.map(([k, label]) => {
      const on = k === value;
      return <Pressable key={k} testID={`${prefix}-${k}`} accessibilityRole="tab" accessibilityState={{ selected: on }} aria-selected={on} onPress={() => { tap(); onChange(k); }} style={[styles.segItem, on && styles.segOn]}>
        <T w="heavy" size={13} color={on ? arena.text : arena.muted} numberOfLines={1}>{label}</T>
      </Pressable>;
    })}
  </Glitter>;
}

/** Gold ribbon label (the chosen subject and chapter on the stage). */
export function Ribbon({ label, sub, onPress, testID }: { label: string; sub?: string; onPress?: () => void; testID?: string }) {
  const body = useMemo(() => <LinearGradient colors={[arena.gold, arena.goldDeep]} style={styles.ribbon}>
    <View style={styles.flex}><T testID={testID ? `${testID}-label` : undefined} w="heavy" size={15} color={arena.badgeInk} numberOfLines={1} style={styles.center}>{label}</T>
      {sub ? <T testID={testID ? `${testID}-sub` : undefined} w="bold" size={11} color={arena.bgDeep} numberOfLines={1} style={styles.center}>{sub}</T> : null}</View>
    {onPress ? <Icon name="chevron-down" size={20} color={arena.badgeInk} /> : null}
  </LinearGradient>, [label, sub, onPress, testID]);
  return onPress ? <Pressable testID={testID} onPress={() => { tap(); onPress(); }} accessibilityRole="button" accessibilityLabel={`${label}. Change subject or chapter`} style={styles.ribbonWrap}>{body}</Pressable> : <View testID={testID} style={styles.ribbonWrap}>{body}</View>;
}

export const arenaInput = { height: 52, borderRadius: 16, paddingHorizontal: 14, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim, color: arena.text, fontFamily: fonts.bold, fontSize: 16 } as const;

const styles = StyleSheet.create({
  bg: { flex: 1, backgroundColor: arena.bg, overflow: "hidden" }, flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" },
  panelSheen: { position: "absolute", top: 0, left: 0, right: 0, height: "55%" },
  panel: { backgroundColor: arena.panel, borderBottomWidth: 4, borderBottomColor: arena.panelEdge },
  panelLift: { backgroundColor: arena.panelEdge, shadowColor: arena.black, shadowOpacity: 0.35, shadowRadius: 10, shadowOffset: { width: 0, height: 6 }, elevation: 5 },
  panelGold: { borderBottomColor: arena.goldDeep }, panelFlat: { borderBottomWidth: 0 },
  hairline: { position: "absolute", top: 0, left: 20, right: 20, height: 1.5 },
  gloss: { position: "absolute", top: 2, left: 3, right: 3, height: "42%", backgroundColor: arena.gloss },
  streak: { position: "absolute", top: -40, bottom: -40, width: 56, left: 0 },
  buttonRow: { flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingHorizontal: 14 }, buttonCopy: { alignItems: "center", flexShrink: 1 },
  inkShadow: { textShadowOffset: { width: 0, height: 1.5 }, textShadowRadius: 1 },
  goldShadow: { textShadowColor: arena.panelEdge, textShadowOffset: { width: 0, height: 2 }, textShadowRadius: 1 },
  back: { width: 46 },
  badge: { minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 5, alignItems: "center", justifyContent: "center", backgroundColor: arena.badge, borderWidth: 1.5, borderColor: arena.badgeInk },
  top: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, minHeight: 56 },
  section: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 4 }, sectionAction: { minHeight: 44, justifyContent: "center", paddingLeft: 12 },
  segment: { flexDirection: "row", gap: 4, padding: 4, backgroundColor: arena.panelEdge },
  segItem: { flex: 1, minHeight: 44, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingHorizontal: 4 },
  segOn: { backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 3, borderBottomColor: arena.tealDeep },
  ribbonWrap: { alignSelf: "center", minWidth: 220, maxWidth: "92%", borderRadius: 14, backgroundColor: arena.goldDeep, paddingBottom: 4 },
  ribbon: { minHeight: 46, borderRadius: 14, flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 16, paddingVertical: 5, borderWidth: 1.5, borderColor: arena.goldDeep },
});

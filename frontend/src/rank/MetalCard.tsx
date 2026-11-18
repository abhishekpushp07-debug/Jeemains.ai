// The Rank Card, after a quiet black metal membership card: soft graphite fading to black, one faint diagonal sheen,
// a hairline diamond across its right side, a small diamond mark by the name, sparkle-silver serif with a twinkling glint
// and blood-red hairlines. Gradients, SVG and text only, so it costs nothing in app size.
import React, { useEffect, useState } from "react";
import { StyleSheet, useWindowDimensions, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Path } from "react-native-svg";
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Pill } from "@/src/components/design";
import { T } from "@/src/components/ui";
import { rankColors as colors, space } from "@/src/theme";
import type { CardRef } from "@/src/shareCard";
import { SERIF } from "./tones";
import { DiamondLine, DiamondMark } from "./Diamond";

const silver = colors.custom_rankSilver, muted = colors.custom_rankSilverMuted, bloodInk = colors.custom_rankBloodInk;
const EDGE = [colors.custom_clear, colors.custom_rankSilverLine, colors.custom_rankShimmer, colors.custom_rankSilverLine, colors.custom_clear] as const;

export function MetalCard({ badge, children, foot, testID, cardRef }: { badge: string; children: React.ReactNode; foot?: React.ReactNode; testID?: string; cardRef?: CardRef }) {
  const narrow = useWindowDimensions().width < 360; // small phones: score caps above the № serial instead of beside it
  return <View style={styles.glow}><View ref={cardRef} collapsable={false} testID={testID} style={styles.card}>
    <LinearGradient colors={[colors.custom_eliteFrom, colors.custom_eliteMid, colors.custom_eliteTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <DiamondLine size={300} style={styles.watermark} />
    <LinearGradient colors={[colors.custom_clear, colors.custom_metalSheenSoft, colors.custom_clear]} locations={[0.3, 0.48, 0.66]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={EDGE} locations={[0, 0.22, 0.5, 0.78, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.edge} />
    <View style={styles.top}>
      <View style={styles.brand}>
        <DiamondMark width={20} />
        <T w="bold" size={11} color={silver} style={styles.track}>JEELIVE.AI</T>
      </View>
      <T w="bold" size={10.5} color={bloodInk} style={[styles.track, { flexShrink: 1 }]} numberOfLines={1}>{badge}</T>
    </View>
    {children}
    {foot ? <View style={[styles.foot, narrow && styles.footStack]}>{foot}</View> : null}
  </View></View>;
}

export const Eyebrow = ({ children }: { children: React.ReactNode }) =>
  <T w="bold" size={10.5} color={muted} style={styles.track}>{children}</T>;

/** A 4-point sparkle star with curved sides. */
const Star = ({ size, x, y }: { size: number; x: number; y: number }) => {
  const c = size / 2;
  return <Svg width={size} height={size} style={{ position: "absolute", left: x, top: y }}>
    <Path d={`M${c} 0Q${c} ${c} ${size} ${c}Q${c} ${c} ${c} ${size}Q${c} ${c} 0 ${c}Q${c} ${c} ${c} 0Z`} fill={colors.custom_rankSparkle} />
  </Svg>;
};

/** Two silver glints beside the big number that slowly trade brightness (still under Reduce Motion). */
function Sparkle() {
  const reduced = useReducedMotion();
  const glow = useSharedValue(1);
  useEffect(() => {
    if (reduced) return;
    glow.value = withRepeat(withSequence(withTiming(0.25, { duration: 1700 }), withTiming(1, { duration: 1700 })), -1);
    return () => cancelAnimation(glow);
  }, [reduced, glow]);
  const big = useAnimatedStyle(() => ({ opacity: glow.value }));
  const small = useAnimatedStyle(() => ({ opacity: 1.25 - glow.value }));
  return <View style={styles.sparkle} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Animated.View style={[StyleSheet.absoluteFill, big]}><Star size={15} x={4} y={0} /></Animated.View>
    <Animated.View style={[StyleSheet.absoluteFill, small]}><Star size={8} x={15} y={18} /></Animated.View>
  </View>;
}

export const SerifBig = ({ children, testID }: { children: string; testID?: string }) => {
  const { width } = useWindowDimensions();
  // Fits one line on every phone (web has no adjustsFontSizeToFit): screen + card padding and the glints, ~0.5em per serif digit.
  const room = Math.min(width, 560) - 2 * space.lg - 2 * space.xl - 26;
  const size = Math.max(22, Math.min(36, Math.floor(room / (children.length * 0.5))));
  return <View style={styles.bigRow}>
    <T testID={testID} color={silver} numberOfLines={1} adjustsFontSizeToFit style={[styles.big, { fontSize: size, lineHeight: Math.round(size * 1.22) }]}>{children}</T>
    <Sparkle />
  </View>;
};

export const SilverCaps = ({ children, testID }: { children: string; testID?: string }) =>
  <T testID={testID} w="semibold" size={12.5} color={silver} numberOfLines={3} style={styles.caps}>{children.toUpperCase().replace(/-/g, "\u2011")}</T>;

/** Blood-red hairline, then the label in light blood red tracked caps (tighter tracking on small phones so numbers stay together). */
export const Hairline = ({ label, testID }: { label: string; testID?: string }) => {
  const narrow = useWindowDimensions().width < 360;
  return <View style={styles.ruleRow}>
    <LinearGradient colors={[colors.custom_rankBlood, colors.custom_rankBloodInk]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.rule} />
    <T testID={testID} w="bold" size={11.5} color={bloodInk} style={[styles.track, narrow && styles.trackTight, { flexShrink: 1 }]} numberOfLines={2}>{label}</T>
  </View>;
};

export const Small = ({ label, value, testID }: { label: string; value: string; testID?: string }) => <View style={styles.small}>
  <Eyebrow>{label.toUpperCase()}</Eyebrow>
  <T testID={testID} color={silver} numberOfLines={1} adjustsFontSizeToFit style={styles.mid}>{value}</T>
</View>;

/** "№ 13,529 / 15,38,468": blood-red №, sparkle-silver serif numbers, bottom right of the card. */
export const Serial = ({ value, of, testID }: { value: string; of?: string; testID?: string }) => <View testID={testID} style={styles.serial}>
  <T color={bloodInk} style={[styles.serif, { fontSize: 13 }]}>№ </T>
  <T color={silver} style={[styles.serif, styles.chrome, { fontSize: 24, lineHeight: 28 }]}>{value}</T>
  {of ? <T color={muted} style={[styles.serif, { fontSize: 13 }]}> / {of}</T> : null}
</View>;

/** Light notes and the actions under the card (Shortlist only where the card leads to colleges).
 *  `onShare` sends the card's photo; the button spins while the photo is made. */
export function CardActions({ notes, onShare, saved, onShortlist, prefix }: {
  notes: (string | undefined | false)[]; onShare: () => Promise<unknown>; saved?: number; onShortlist?: () => void; prefix: string;
}) {
  const [busy, setBusy] = useState(false);
  const share = async () => {
    if (busy) return;
    setBusy(true);
    try { await onShare(); } catch { /* the share sheet closed or WhatsApp refused: nothing to undo */ } finally { setBusy(false); }
  };
  return <View style={{ gap: space.md }}>
    <View style={{ gap: 4 }}>
      {notes.filter(Boolean).map(n => <T key={n as string} size={12.5} color={colors.custom_softText}>{n}</T>)}
    </View>
    <View style={styles.actions}>
      <Pill testID={`${prefix}-share`} size="sm" icon="whatsapp" label="WhatsApp" accessibilityLabel="Card WhatsApp par bhejo" bg={colors.custom_whatsapp} ink={colors.onBrandPrimary} busy={busy} onPress={share} style={{ flex: 1 }} />
      {onShortlist ? <Pill testID={`${prefix}-shortlist-open`} size="sm" icon="playlist-check" label={`Shortlist ${saved ?? 0}`} onPress={onShortlist} bg={colors.custom_cardRaised} ink={colors.onSurface} style={[{ flex: 1 }, styles.outline]} /> : null}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  glow: { borderRadius: 22, shadowColor: colors.custom_rankBg, shadowOpacity: 0.6, shadowRadius: 22, shadowOffset: { width: 0, height: 10 }, elevation: 10, backgroundColor: colors.custom_eliteMid },
  outline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  card: { borderRadius: 22, padding: space.xl, gap: space.lg, overflow: "hidden", backgroundColor: colors.custom_eliteMid, borderWidth: 1, borderColor: colors.custom_eliteLine },
  // The hairline diamond sits half off the right edge, like the watermark on a metal card.
  watermark: { position: "absolute", right: -120, top: -24 },
  brand: { flexDirection: "row", alignItems: "center", gap: space.sm },
  edge: { position: "absolute", top: 0, left: 0, right: 0, height: 1.5 },
  top: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  track: { letterSpacing: 3 },
  trackTight: { letterSpacing: 1.4 },
  caps: { letterSpacing: 1.6 },
  serif: { fontFamily: SERIF },
  chrome: { textShadowColor: colors.custom_rankChrome, textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 8 },
  bigRow: { flexDirection: "row", alignItems: "flex-start" },
  big: { flexShrink: 1, fontFamily: SERIF, fontSize: 36, lineHeight: 44, letterSpacing: 0.5, textShadowColor: colors.custom_rankChrome, textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 12 },
  sparkle: { width: 24, height: 26, marginLeft: 2 },
  mid: { fontFamily: SERIF, fontSize: 19, lineHeight: 24 },
  ruleRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  rule: { width: 26, height: 1.5 },
  small: { flexGrow: 1, minWidth: "40%", gap: 2 },
  foot: { flexDirection: "row", alignItems: "flex-end", gap: space.md, borderTopWidth: 1, borderTopColor: colors.custom_rankLine, paddingTop: space.md },
  footStack: { flexDirection: "column", alignItems: "stretch", gap: space.sm },
  serial: { flexDirection: "row", alignItems: "baseline" },
  actions: { flexDirection: "row", gap: space.sm },
});

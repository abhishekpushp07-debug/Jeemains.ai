// The Rank Card: brushed graphite, a navy glow, one diagonal sheen, silver serif and an electric-blue hairline.
// Gradients and text only, so it costs nothing in app size.
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Pill } from "@/src/components/design";
import { T } from "@/src/components/ui";
import { rankColors as colors, space } from "@/src/theme";
import { SERIF } from "./tones";

type Stops = readonly [string, string, ...string[]];
const BRUSH = Array.from({ length: 44 }, (_, i) => (i % 2 ? colors.custom_clear : colors.custom_rankBrush)) as unknown as Stops;
const silver = colors.custom_rankSilver, muted = colors.custom_rankSilverMuted, blue = colors.custom_rankBlue;

export function MetalCard({ badge, children, foot, testID }: { badge: string; children: React.ReactNode; foot?: React.ReactNode; testID?: string }) {
  return <View style={styles.glow}><View testID={testID} style={styles.card}>
    <LinearGradient colors={[colors.custom_rankFrom, colors.custom_rankMid, colors.custom_rankTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={BRUSH} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={[colors.custom_clear, colors.custom_rankGlow]} start={{ x: 0.35, y: 0.15 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <LinearGradient colors={[colors.custom_clear, colors.custom_rankSheen, colors.custom_clear]} locations={[0.3, 0.48, 0.66]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <View style={styles.top}>
      <T w="bold" size={11} color={silver} style={styles.track}>JEELIVE.AI</T>
      <T w="bold" size={10.5} color={blue} style={styles.track}>{badge}</T>
    </View>
    {children}
    {foot ? <View style={styles.foot}>{foot}</View> : null}
  </View></View>;
}

export const Eyebrow = ({ children }: { children: React.ReactNode }) =>
  <T w="bold" size={10.5} color={muted} style={styles.track}>{children}</T>;

export const SerifBig = ({ children, testID }: { children: string; testID?: string }) =>
  <T testID={testID} color={silver} numberOfLines={1} adjustsFontSizeToFit style={styles.big}>{children}</T>;

export const SilverCaps = ({ children, testID }: { children: string; testID?: string }) =>
  <T testID={testID} w="semibold" size={12.5} color={silver} numberOfLines={2} style={styles.caps}>{children.toUpperCase()}</T>;

export const BlueRule = ({ label, testID }: { label: string; testID?: string }) => <View style={styles.ruleRow}>
  <View style={styles.rule} />
  <T testID={testID} w="bold" size={11.5} color={blue} style={[styles.track, { flexShrink: 1 }]} numberOfLines={2}>{label}</T>
</View>;

export const Small = ({ label, value, testID }: { label: string; value: string; testID?: string }) => <View style={styles.small}>
  <Eyebrow>{label.toUpperCase()}</Eyebrow>
  <T testID={testID} color={silver} numberOfLines={1} adjustsFontSizeToFit style={styles.mid}>{value}</T>
</View>;

/** "№ 13,529 / 15,38,468" in blue serif, bottom right of the card. */
export const Serial = ({ value, of, testID }: { value: string; of?: string; testID?: string }) => <View testID={testID} style={styles.serial}>
  <T color={blue} style={[styles.serif, { fontSize: 13 }]}>№ </T>
  <T color={blue} style={[styles.serif, { fontSize: 24, lineHeight: 28 }]}>{value}</T>
  {of ? <T color={blue} style={[styles.serif, { fontSize: 13 }]}> / {of}</T> : null}
</View>;

/** Light notes and the two actions under the card. */
export function CardActions({ notes, onShare, saved, onShortlist, prefix }: {
  notes: (string | undefined | false)[]; onShare: () => void; saved: number; onShortlist: () => void; prefix: string;
}) {
  return <View style={{ gap: space.md }}>
    <View style={{ gap: 4 }}>
      {notes.filter(Boolean).map(n => <T key={n as string} size={12.5} color={colors.custom_softText}>{n}</T>)}
    </View>
    <View style={styles.actions}>
      <Pill testID={`${prefix}-share`} size="sm" icon="whatsapp" label="WhatsApp" accessibilityLabel="WhatsApp par bhejo" bg={colors.custom_whatsapp} ink={colors.onBrandPrimary} onPress={onShare} style={{ flex: 1 }} />
      <Pill testID={`${prefix}-shortlist-open`} size="sm" icon="star" label={`Shortlist ${saved}`} onPress={onShortlist} bg={colors.custom_cardRaised} ink={colors.onSurface} style={[{ flex: 1 }, styles.outline]} />
    </View>
  </View>;
}

const styles = StyleSheet.create({
  glow: { borderRadius: 22, shadowColor: colors.custom_rankBlue, shadowOpacity: 0.22, shadowRadius: 26, shadowOffset: { width: 0, height: 10 }, elevation: 10, backgroundColor: colors.custom_rankMid },
  outline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  card: { borderRadius: 22, padding: space.xl, gap: space.lg, overflow: "hidden", backgroundColor: colors.custom_rankMid, borderWidth: 1, borderColor: colors.custom_rankLine },
  top: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  track: { letterSpacing: 3 },
  caps: { letterSpacing: 1.6 },
  serif: { fontFamily: SERIF },
  big: { fontFamily: SERIF, fontSize: 36, lineHeight: 44, letterSpacing: 0.5, textShadowColor: colors.custom_rankChrome, textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 10 },
  mid: { fontFamily: SERIF, fontSize: 19, lineHeight: 24 },
  ruleRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  rule: { width: 26, height: 1.5, backgroundColor: colors.custom_rankBlue },
  small: { flexGrow: 1, minWidth: "40%", gap: 2 },
  foot: { flexDirection: "row", alignItems: "flex-end", gap: space.md, borderTopWidth: 1, borderTopColor: colors.custom_rankLine, paddingTop: space.md },
  serial: { flexDirection: "row", alignItems: "baseline" },
  actions: { flexDirection: "row", gap: space.sm },
});

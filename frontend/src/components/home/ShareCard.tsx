// The last card on Home: a royal-blue invite with the share buttons right on its face.
import React, { useId } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Defs, RadialGradient, Rect, Stop } from "react-native-svg";
import { IconName, Press, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { shareAppAnywhere, shareAppWhatsApp } from "@/src/shareApp";

const PERKS: { icon: IconName; title: string; line: string }[] = [
  { icon: "lightning-bolt", title: "Rapid Fire", line: "revise in 15-second cards" },
  { icon: "bullseye-arrow", title: "Rank", line: "know your rank & colleges" },
  { icon: "school-outline", title: "Dream college", line: "aim with the marks you need" },
  { icon: "calendar-check-outline", title: "Mocks + AITS", line: "raise your chances daily" },
];

export function ShareCard() {
  const narrow = useWindowDimensions().width < 360;
  const glow = "shareGlow" + useId().replace(/[^a-z0-9]/gi, "");
  return <View testID="home-share-card" style={styles.card}>
    <LinearGradient colors={[colors.custom_royalFrom, colors.custom_royalMid, colors.custom_royalTo]} locations={[0, 0.5, 1]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    {/* Explicit stopOpacity: native SVG ignores alpha inside stopColor. */}
    <Svg style={StyleSheet.absoluteFill} width="100%" height="100%" pointerEvents="none">
      <Defs>
        <RadialGradient id={glow} cx="100%" cy="0%" rx="85%" ry="50%" fx="100%" fy="0%">
          <Stop offset="0" stopColor={colors.custom_royalGlow} stopOpacity={0.6} />
          <Stop offset="1" stopColor={colors.custom_royalGlow} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect x="0" y="0" width="100%" height="100%" fill={`url(#${glow})`} />
    </Svg>

    <View style={styles.top}>
      <View style={styles.glassChip}>
        <Glyph name="heart" size={12} color={colors.onSurfaceInverse} />
        <T w="bold" size={10.5} color={colors.onSurfaceInverse} style={styles.caps} numberOfLines={1}>{narrow ? "100% FREE" : "100% FREE · FOREVER"}</T>
      </View>
      <View testID="home-share-dna" style={styles.dna}>
        <Glyph name="dna" size={13} color={colors.custom_royalDeep} />
        <T w="heavy" size={10} color={colors.custom_royalDeep} style={{ letterSpacing: 1 }}>PYQ DNA</T>
      </View>
    </View>

    <View style={{ gap: 6 }}>
      <T testID="home-share-title" w="heavy" size={narrow ? 22 : 25} color={colors.onSurfaceInverse} style={{ letterSpacing: -0.4 }}>Share it with your friends.</T>
      <T size={narrow ? 13 : 14} color={colors.custom_royalInk} style={{ lineHeight: narrow ? 19 : 20 }}>
        Built by AI after deeply analysing <T w="heavy" size={narrow ? 13 : 14} color={colors.onSurfaceInverse}>4,000+ PYQs</T>, so every question carries real PYQ DNA. A seriously good product, and completely free.
      </T>
    </View>

    <View style={styles.grid}>
      {/* Under 360px each perk gets a full row, so no title or line is cut. */}
      {PERKS.map(p => <View key={p.title} style={[styles.perk, narrow && styles.perkWide]}>
        <View style={styles.perkIcon}><Glyph name={p.icon} size={17} color={colors.onSurfaceInverse} stroke={1.6} /></View>
        <View style={{ flex: 1, minWidth: 0 }}>
          <T w="bold" size={13} color={colors.onSurfaceInverse} numberOfLines={1}>{p.title}</T>
          <T size={11} color={colors.custom_royalInk} numberOfLines={2}>{p.line}</T>
        </View>
      </View>)}
    </View>

    <View testID="home-share-goal" style={styles.goal}>
      <T w="heavy" size={narrow ? 26 : 30} color={colors.onSurfaceInverse} style={{ letterSpacing: -1 }}>200+</T>
      <T size={12.5} color={colors.custom_royalInk} style={{ flex: 1, lineHeight: 17 }}>
        marks of questions in every shift should feel familiar. <T w="bold" size={12.5} color={colors.onSurfaceInverse}>Same concept, only the numbers change.</T> That is the AI&apos;s target.
      </T>
    </View>

    <View style={styles.actions}>
      <Pill testID="home-share-whatsapp" icon="whatsapp" label={narrow ? "Share" : "Share on WhatsApp"} bg={colors.onSurfaceInverse} ink={colors.custom_royalDeep}
        style={styles.cta} onPress={shareAppWhatsApp} accessibilityLabel="Share JEELIVE.AI with friends on WhatsApp" />
      <Press testID="home-share-more" onPress={shareAppAnywhere} accessibilityLabel="Share JEELIVE.AI in another app" scaleTo={0.94} style={styles.more}>
        <Glyph name="share-variant" size={20} color={colors.onSurfaceInverse} />
      </Press>
    </View>
    <T size={11} color={colors.custom_royalInk} style={{ opacity: 0.85 }}>Every share helps one more aspirant prepare for free. The 200+ goal is a practice target, not a guarantee.</T>
  </View>;
}

const styles = StyleSheet.create({
  card: { borderRadius: 28, padding: 20, gap: space.lg, overflow: "hidden", backgroundColor: colors.custom_royalMid,
    shadowColor: colors.custom_royalMid, shadowOpacity: 0.35, shadowRadius: 18, shadowOffset: { width: 0, height: 8 }, elevation: 6 },
  top: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  caps: { letterSpacing: 1.6 },
  glassChip: { flexDirection: "row", alignItems: "center", gap: 6, height: 28, paddingHorizontal: 11, borderRadius: 999, borderWidth: 1,
    borderColor: colors.custom_royalLine, backgroundColor: colors.custom_royalGlass, flexShrink: 1 },
  dna: { flexDirection: "row", alignItems: "center", gap: 4, height: 26, paddingHorizontal: 9, borderRadius: 999, backgroundColor: colors.custom_royalInk },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  perk: { flexGrow: 1, flexBasis: "46%", flexDirection: "row", alignItems: "center", gap: 9, padding: 10, borderRadius: 16,
    borderWidth: 1, borderColor: colors.custom_royalLine, backgroundColor: colors.custom_royalGlass },
  perkWide: { flexBasis: "100%" },
  perkIcon: { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_royalGlass },
  goal: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 12, paddingHorizontal: 14, borderRadius: 18,
    borderLeftWidth: 3, borderLeftColor: colors.onSurfaceInverse, backgroundColor: colors.custom_royalGlass },
  actions: { flexDirection: "row", alignItems: "center", gap: 10 },
  cta: { flex: 1, borderRadius: 16 },
  more: { width: 52, height: 52, borderRadius: 16, alignItems: "center", justifyContent: "center", borderWidth: 1,
    borderColor: colors.custom_royalLine, backgroundColor: colors.custom_royalGlass },
});

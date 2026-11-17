import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { IconName, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, radius, space } from "@/src/theme";
import { fmtClock } from "@/src/navigation";

/** CRED-style 2×2 grid: soft hairline tiles, icon in a circle, caps label, value with chevron. */
export type GridItem = { id: string; icon: IconName; label: string; value: string; badge?: string; to: string };
export function ExamGrid({ items }: { items: GridItem[] }) {
  const router = useRouter();
  const narrow = useWindowDimensions().width < 360;
  const rows = Array.from({ length: Math.ceil(items.length / 2) }, (_, r) => items.slice(r * 2, r * 2 + 2));
  return <View testID="home-exam-grid" style={styles.grid}>
    {rows.map((row, r) => <View key={r} style={styles.gridRow}>
      {row.map(it => <Press key={it.id} testID={"home-tile-" + it.id} onPress={() => router.push(it.to as any)} accessibilityLabel={`${it.label}. ${it.value}`} scaleTo={0.97} style={styles.tilePress}>
        <LinearGradient colors={[colors.custom_chipFrom, colors.custom_chipTo]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={[styles.tile, narrow && styles.tileNarrow]}>
          <View style={styles.tileTop}>
            <View style={[styles.tileIcon, narrow && styles.tileIconNarrow]}><Glyph name={it.icon} size={narrow ? 22 : 26} color={colors.onSurface} stroke={1.4} /></View>
            {it.badge ? <LinearGradient testID={`home-tile-${it.id}-badge`} colors={[colors.custom_chipFrom, colors.custom_successSoft]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.badge}>
              <T testID={`home-tile-${it.id}-badge-label`} w="bold" size={10} color={colors.success} style={{ letterSpacing: 1.2 }}>{it.badge}</T>
            </LinearGradient> : null}
          </View>
          <View style={{ flex: 1 }} />
          <T testID={`home-tile-${it.id}-title`} w="heavy" size={narrow ? 15 : 17} color={colors.custom_royalMaroon} style={styles.examName} numberOfLines={1}>{it.label}</T>
          <View style={styles.valueRow}>
            <T testID={`home-tile-${it.id}-description`} w="semibold" size={narrow ? 12.5 : 13.5} color={colors.muted} numberOfLines={1} style={{ flexShrink: 1 }}>{it.value}</T>
            <Glyph name="chevron-right" size={15} color={colors.muted} />
          </View>
        </LinearGradient>
      </Press>)}
    </View>)}
  </View>;
}

/** "For you" row: soft grey circles with hairline icons and an optional black caps badge. */
export type CircleItem = { id: string; icon: IconName; label: string; badge?: string; onPress: () => void; testID: string; badgeTestID?: string };
export function ForYou({ items }: { items: CircleItem[] }) {
  return <View testID="home-for-you" style={styles.circles}>
    {items.map(it => <Press key={it.id} testID={it.testID} onPress={it.onPress} accessibilityLabel={it.label.replace("\n", " ") + (it.badge ? `, ${it.badge}` : "")} scaleTo={0.94} style={styles.circleItem}>
      <View style={styles.circle}>
        <Glyph name={it.icon} size={28} color={colors.onSurface} stroke={1.4} />
        {it.badge ? <View style={styles.circleBadge}><T testID={it.badgeTestID} w="bold" size={9.5} color={colors.onSurfaceInverse} style={{ letterSpacing: 0.8 }} numberOfLines={1}>{it.badge}</T></View> : null}
      </View>
      <T size={13} w="medium" color={colors.onSurface} style={styles.circleLabel} numberOfLines={2}>{it.label}</T>
    </Press>)}
  </View>;
}

/** Bill-style continue card: grey band on top, black action on the right with a small caps due line. */
export function ContinueCard({ attempt, onPress }: { attempt: any; onPress: () => void }) {
  const left = attempt.remaining_seconds ? fmtClock(Math.round(attempt.remaining_seconds)) + " left" : "";
  return <Press testID="home-continue-attempt" onPress={onPress} accessibilityLabel={`Resume ${attempt.title}`} scaleTo={0.985} style={styles.bill}>
    <View style={styles.band}>
      <Glyph name="check-circle-outline" size={15} color={colors.success} />
      <T size={12.5} color={colors.custom_softText} numberOfLines={1} style={{ flexShrink: 1 }}>your answers are saved · pick up where you left</T>
    </View>
    <View style={styles.billRow}>
      <View style={styles.billIcon}><Glyph name="clipboard-text-outline" size={22} color={colors.onSurface} stroke={1.5} /></View>
      <View style={{ flex: 1, gap: 2 }}>
        <T w="semibold" size={15} numberOfLines={1}>{attempt.title}</T>
        <T size={12.5} color={colors.muted} numberOfLines={1}>{attempt.saved_answers}/{attempt.count} saved</T>
      </View>
      <View style={{ alignItems: "center", gap: 6 }}>
        <View testID="home-continue-resume" style={styles.resume}><T w="bold" size={14} color={colors.onSurfaceInverse}>Resume</T></View>
        {left ? <T w="bold" size={9.5} color={colors.custom_timerAmber} style={{ letterSpacing: 1.2 }}>{left.toUpperCase()}</T> : null}
      </View>
    </View>
  </Press>;
}

/** Soft gradient promo with a big typographic number, like a fintech offer banner. */
export function PromoBanner({ onPress, days }: { onPress: () => void; days: number }) {
  // Below 360px the big number would squeeze the copy, so the copy gets the full width.
  const narrow = useWindowDimensions().width < 360;
  return <LinearGradient testID="home-promo" colors={[colors.custom_promoFrom, colors.custom_promoTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.promo}>
    <View style={{ flex: 1, gap: 6 }}>
      <T w="bold" size={10.5} color={colors.custom_promoInk} style={{ letterSpacing: narrow ? 1.2 : 2 }} numberOfLines={1}>AI ASTRA · 100% AI</T>
      <T testID="home-promo-title" w="heavy" size={narrow ? 16 : 17}>score 200+ with AI.{"\n"}{days ? `${days} daily mocks` : "daily full mocks"}, free.</T>
      <Press testID="home-promo-cta" onPress={onPress} accessibilityLabel="Know more about the All India series" style={styles.promoBtn}>
        <T w="bold" size={13} color={colors.onSurfaceInverse}>Know more</T>
      </Press>
    </View>
    {narrow ? null : <T w="heavy" size={50} color={colors.custom_promoInk} style={styles.promoNum} accessibilityElementsHidden importantForAccessibility="no">200+</T>}
  </LinearGradient>;
}

/** Explore pills: lowercase labels with small coloured hairline icons. */
export type ChipItem = { id: string; icon: IconName; label: string; tint: string; onPress: () => void };
export function ExploreChips({ items }: { items: ChipItem[] }) {
  return <View testID="home-explore" style={styles.chips}>
    {items.map(it => <Press key={it.id} testID={"home-explore-" + it.id} onPress={it.onPress} accessibilityLabel={it.label} scaleTo={0.96}>
      <LinearGradient colors={[colors.custom_chipFrom, colors.custom_chipTo]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.chip}>
        <Glyph name={it.icon} size={19} color={it.tint} stroke={1.7} />
        <T w="semibold" size={15}>{it.label}</T>
      </LinearGradient>
    </Press>)}
  </View>;
}

const styles = StyleSheet.create({
  grid: { gap: space.md },
  gridRow: { flexDirection: "row", gap: space.md },
  tilePress: { flex: 1, minWidth: 0 },
  tile: { height: 168, borderRadius: 24, borderWidth: 1, borderColor: colors.custom_cardLineStrong, padding: space.lg, paddingBottom: 16 },
  tileNarrow: { height: 150, padding: 14 },
  tileTop: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 4 },
  tileIcon: { width: 50, height: 50, borderRadius: 25, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  tileIconNarrow: { width: 42, height: 42, borderRadius: 21 },
  badge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  caps: { letterSpacing: 2 },
  examName: { letterSpacing: 1 },
  valueRow: { flexDirection: "row", alignItems: "center", gap: 2, marginTop: 2 },
  circles: { flexDirection: "row", justifyContent: "space-between" },
  circleItem: { flex: 1, alignItems: "center", gap: 10, minWidth: 0 },
  circle: { width: 68, height: 68, borderRadius: 34, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  circleBadge: { position: "absolute", bottom: -9, alignSelf: "center", backgroundColor: colors.onSurface, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3, maxWidth: 84 },
  circleLabel: { textAlign: "center", lineHeight: 17, marginTop: 2 },
  bill: { borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, overflow: "hidden" },
  band: { flexDirection: "row", alignItems: "center", gap: 6, justifyContent: "center", paddingVertical: 10, paddingHorizontal: space.lg, backgroundColor: colors.custom_cardRaised, borderBottomWidth: 1, borderBottomColor: colors.custom_cardLine },
  billRow: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.lg },
  billIcon: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  resume: { height: 42, paddingHorizontal: 18, borderRadius: 12, backgroundColor: colors.onSurface, alignItems: "center", justifyContent: "center" },
  promo: { borderRadius: 22, padding: 20, flexDirection: "row", alignItems: "center", gap: space.md, overflow: "hidden" },
  promoBtn: { alignSelf: "flex-start", marginTop: 6, minHeight: 44, paddingHorizontal: 18, borderRadius: 12, backgroundColor: colors.onSurface, alignItems: "center", justifyContent: "center" },
  promoNum: { lineHeight: 56, letterSpacing: -2, opacity: 0.9 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  chip: { flexDirection: "row", alignItems: "center", gap: 8, height: 52, paddingHorizontal: 18, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
});

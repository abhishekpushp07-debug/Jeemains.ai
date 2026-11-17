// One college in the College predictor lists (JEE, COMEDK, BITSAT) as its own card that reads like a button: the chance
// colour down the left edge, medal + name, type and chance tags, the course, three stat boxes, and a footer saying what is
// inside next to a bright "Cutoff dekho ›" button in the tool's colour. The whole card opens the details; the star saves it.
// Cards already opened say "Dekha". Until the student has opened any college once, the first card's button breathes and a
// hint above the list says to tap.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import Animated, { cancelAnimation, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withSequence, withTiming } from "react-native-reanimated";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { useAccent } from "./accent";
import { StarButton } from "./controls";
import { Medal, MedalWash } from "./Medal";
import type { DreamToggle } from "@/src/dream/useDreamToggle";

export type Stat = { label: string; value: string; sub?: string; ink?: string; testID?: string };

export function CollegeCard({ testID, rank, edge, title, tags, sub, line, stats, note, teaser, viewed, pulse, open, onPress, saved, onStar, a11y, children, dream }: {
  testID: string; rank?: number; edge: string; title: string; tags?: React.ReactNode; sub: string; line?: string; stats: Stat[];
  note?: React.ReactNode; teaser: string; viewed?: boolean; pulse?: boolean; open?: boolean; onPress: () => void;
  saved: boolean; onStar: () => void; a11y: string; children?: React.ReactNode; dream?: DreamToggle;
}) {
  return <View style={[styles.card, rank && rank <= 3 ? styles.cardTop : null]}>
    <MedalWash n={rank} />
    <View style={[styles.edge, { backgroundColor: edge }]} />
    <Press testID={testID} onPress={onPress} scaleTo={0.985} accessibilityRole="button" accessibilityLabel={`${a11y}. Cutoff dekho`}
      accessibilityState={open === undefined ? undefined : { expanded: open }} style={styles.press}>
      <View style={styles.head}>
        {rank ? <Medal n={rank} testID={`${testID}-medal`} /> : null}
        <View style={{ flex: 1, gap: 4, paddingRight: dream ? 40 : 0 }}>
          <T w="bold" size={15} numberOfLines={2} style={styles.title}>{title}</T>
          {tags ? <View style={styles.tags}>{tags}</View> : null}
          <T size={13.5} color={colors.custom_softText} numberOfLines={2}>{sub}</T>
          {line ? <T size={11.5} color={colors.muted} numberOfLines={2}>{line}</T> : null}
        </View>
      </View>
      <View style={styles.stats}>
        {stats.map((s, i) => <View key={s.label} testID={s.testID} style={[styles.stat, i > 0 && styles.statLine]}>
          <T w="bold" size={9.5} color={colors.custom_eyebrow} style={styles.statLabel} numberOfLines={1}>{s.label}</T>
          <T w="heavy" size={14} color={s.ink ?? colors.onSurface} numberOfLines={2}>{s.value}</T>
          {s.sub ? <T size={10.5} color={colors.muted} numberOfLines={2}>{s.sub}</T> : null}
        </View>)}
      </View>
      {note}
      {dream?.msg ? <T testID={`${testID}-dream-msg`} w="semibold" size={12} color={dream.on ? colors.custom_fBloodText : colors.custom_flame}>{dream.msg}</T> : null}
      {children}
      <View style={styles.foot}>
        <View style={styles.teaser}>
          <Glyph name={viewed ? "check-circle" : "chart-timeline-variant"} size={15} color={viewed ? colors.success : colors.custom_eyebrow} />
          <T testID={viewed ? `${testID}-viewed` : undefined} size={11.5} color={viewed ? colors.success : colors.custom_softText} numberOfLines={2} style={{ flex: 1 }}>
            {viewed ? `Dekha · ${teaser}` : teaser}
          </T>
        </View>
        <Cta testID={`${testID}-cta`} open={open} pulse={pulse} />
      </View>
    </Press>
    <View style={styles.star}>
      <StarButton saved={saved} onPress={onStar} testID={`${testID}-star`} />
      {dream ? <Press testID={`${testID}-dream`} onPress={dream.toggle} scaleTo={0.92} accessibilityRole="button" accessibilityState={{ selected: dream.on, busy: dream.busy }}
        accessibilityLabel={dream.on ? `${title} dream se hatao` : `${title} ko dream college banao`}
        style={[styles.dream, dream.on && { ...dreamGlow, backgroundColor: colors.custom_fBlood, borderColor: colors.custom_fBlood, shadowColor: colors.custom_fBlood }]}>
        {dream.busy ? <ActivityIndicator size="small" color={colors.custom_fBloodText} />
          : <Glyph name="bullseye-arrow" size={17} color={dream.on ? colors.onBrandPrimary : colors.custom_fBloodText} />}
        <T w="heavy" size={7.5} color={dream.on ? colors.onBrandPrimary : colors.custom_fBloodText} style={{ letterSpacing: 0.6 }}>DREAM</T>
      </Press> : null}
    </View>
  </View>;
}

/** "Cutoff dekho ›" in the tool's colour; breathes gently while `pulse` (never with Reduce Motion). */
function Cta({ testID, open, pulse }: { testID: string; open?: boolean; pulse?: boolean }) {
  const a = useAccent();
  const reduced = useReducedMotion();
  const s = useSharedValue(1);
  const live = !!pulse && !reduced;
  useEffect(() => {
    if (!live) { cancelAnimation(s); s.value = 1; return; }
    s.value = withRepeat(withSequence(withTiming(1.07, { duration: 650 }), withTiming(1, { duration: 650 })), -1);
    return () => cancelAnimation(s);
  }, [live, s]);
  const breathe = useAnimatedStyle(() => ({ transform: [{ scale: s.value }] }));
  const bg = a?.ink ?? colors.brandPrimary, ink = a?.on ?? colors.onBrandPrimary;
  return <Animated.View testID={testID} style={[styles.cta, { backgroundColor: bg }, live && { ...ctaGlow, shadowColor: bg }, breathe]}>
    <T w="heavy" size={13} color={ink} numberOfLines={1}>{open ? "Band karo" : "Cutoff dekho"}</T>
    <Glyph name={open ? "chevron-up" : "chevron-right"} size={16} color={ink} stroke={2.2} />
  </Animated.View>;
}

/** Above a college list: tells the student to tap a card; after they have opened some, counts them. */
export function TapHint({ testID, viewed, what = "college" }: { testID: string; viewed: number; what?: string }) {
  const a = useAccent();
  const ink = a?.ink ?? colors.brandPrimary;
  return <View testID={testID} style={[styles.hint, a && { borderColor: a.line, backgroundColor: a.soft }]}>
    <View style={[styles.hintIcon, { backgroundColor: ink }]}>
      <Glyph name={viewed ? "check-all" : "gesture-tap"} size={20} color={a?.on ?? colors.onBrandPrimary} />
    </View>
    <View style={{ flex: 1, gap: 2 }}>
      <T testID={`${testID}-title`} w="heavy" size={14}>{viewed ? `${viewed} ${what} dekhe, shabaash!` : `Kisi bhi ${what} card par tap karo`}</T>
      <T size={12} color={colors.custom_softText}>{viewed ? "Aur dekho. Sahi choice wahi jo poora data dekh kar ho." : "Har round ka cutoff, seats aur 2025 se trend: sab andar hai."}</T>
    </View>
  </View>;
}

const SEEN = "rank.cta.seen.v1";
/** `pulse` until the student opens any college for the first time (remembered on the phone); `viewed` = opened this visit. */
export function useCardViews() {
  const [seen, setSeen] = useState<boolean | null>(null);
  const [viewed, setViewed] = useState<Set<string>>(() => new Set());
  useEffect(() => { storage.getItem<string | null>(SEEN, null).then(v => setSeen(!!v)); }, []);
  const mark = (id: string) => {
    setViewed(v => (v.has(id) ? v : new Set(v).add(id)));
    if (!seen) { setSeen(true); storage.setItem(SEEN, "1"); }
  };
  return { pulse: seen === false && viewed.size === 0, viewed, mark };
}

/** Section title between card groups, e.g. "BAS THODA SA DOOR". */
export function CardsHeading({ icon, title, sub, ink = colors.custom_eyebrow }: { icon: React.ComponentProps<typeof Glyph>["name"]; title: string; sub?: string; ink?: string }) {
  return <View style={styles.heading}>
    <Glyph name={icon} size={16} color={ink} />
    <View style={{ flex: 1 }}>
      <T w="bold" size={11} color={ink} style={{ letterSpacing: 2 }}>{title}</T>
      {sub ? <T size={11.5} color={colors.muted}>{sub}</T> : null}
    </View>
  </View>;
}

export const cardStyles = StyleSheet.create({ list: { gap: space.md } });

/** The breathing CTA's glow, spread into one inline style with its colour (web draws the blur, Android gets elevation). */
const ctaGlow = { shadowOpacity: 0.7, shadowRadius: 12, shadowOffset: { width: 0, height: 0 }, elevation: 6 };
const dreamGlow = { shadowOpacity: 0.7, shadowRadius: 10, shadowOffset: { width: 0, height: 0 }, elevation: 5 };

const styles = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, overflow: "hidden" },
  cardTop: { borderColor: colors.custom_qFreshLine },
  edge: { position: "absolute", left: 0, top: 0, bottom: 0, width: 4 },
  press: { gap: space.md, paddingVertical: 14, paddingLeft: 16, paddingRight: 14 },
  head: { flexDirection: "row", gap: space.sm, alignItems: "flex-start" },
  title: { paddingRight: 34 }, // room for the star in the corner
  tags: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 6 },
  stats: { flexDirection: "row", borderRadius: 12, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised, overflow: "hidden" },
  stat: { flex: 1, minWidth: 0, gap: 2, paddingVertical: 8, paddingHorizontal: 9 },
  statLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  statLabel: { letterSpacing: 0.8 },
  foot: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingTop: space.md, borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  teaser: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 6 },
  cta: { flexDirection: "row", alignItems: "center", gap: 2, minHeight: 38, paddingLeft: 14, paddingRight: 10, borderRadius: radius.pill },
  star: { position: "absolute", top: 4, right: 4, alignItems: "center", gap: 2 },
  dream: { width: 40, height: 44, borderRadius: 12, borderWidth: 1, borderColor: colors.custom_fBloodLine, backgroundColor: colors.custom_fBloodSoft,
    alignItems: "center", justifyContent: "center", gap: 1 },
  hint: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: 18, borderWidth: 1,
    borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  hintIcon: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  heading: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingTop: space.sm },
});

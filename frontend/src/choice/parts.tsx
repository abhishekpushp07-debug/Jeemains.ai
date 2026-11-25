// The small parts of Student Choice's screens: a tick, a question as it is listed (never its options), the bar at the
// bottom that says how big the paper is, and the paper's make-up subject by subject.
import React, { memo, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { MathText } from "@/src/components/MathText";
import { Glyph } from "@/src/components/Glyph";
import { Pill } from "@/src/components/design";
import { Press, T } from "@/src/components/ui";
import { colors, space, subjectColor } from "@/src/theme";
import { useCached } from "@/src/useCached";
import { Bank, Counts, Question, SHORT, SUBJECTS, Stem, getBank, minutesFor, timeLabel, totalOf } from "./api";

/** The bank, kept on the phone for a few minutes (it is the same for every student). */
export const useBank = (uid?: string) => useCached<Bank>(uid ? "choice.bank" : null, getBank(uid || ""));

export function Tick({ on, size = 26 }: { on: boolean; size?: number }) {
  return <View style={[styles.tick, { width: size, height: size, borderRadius: size / 2 }, on && styles.tickOn]}>
    {on ? <Glyph name="check" size={size * 0.62} color={colors.onSurfaceInverse} stroke={2.6} /> : null}
  </View>;
}

// A wide question shrinks to the card's width; a short one is not blown up past this many times its printed size.
const LARGEST = 1.25;
/** One of a question's pictures at the card's width. Its box is kept before the picture arrives, so the list does not jump. */
function StemPicture({ p, width, testID }: { p: Stem; width: number; testID: string }) {
  const [size, setSize] = useState(p.w && p.h ? { w: p.w, h: p.h } : null);
  const [failed, setFailed] = useState(false);
  if (failed) return <T testID={`${testID}-failed`} size={12.5} color={colors.muted}>Is sawaal ki picture load nahi hui.</T>;
  const scale = size ? Math.min(LARGEST, width / size.w) : 1;
  const w = size ? Math.round(size.w * scale) : width, h = size ? Math.round(size.h * scale) : Math.round(width * 0.24);
  return <Image testID={testID} source={{ uri: p.url }} style={{ width: w, height: h }} contentFit="contain" transition={0} cachePolicy="memory-disk" accessible={false}
    onLoad={e => { if (!size && e.source?.width && e.source?.height) setSize({ w: e.source.width / 2, h: e.source.height / 2 }); }} onError={() => setFailed(true)} />;
}

/** A question in the list: its number, its kind, and its words or pictures. A tap ticks it. */
export const QuestionCard = memo(function QuestionCard({ q, k, on, width, onToggle }: { q: Question; k: number; on: boolean; width: number; onToggle: (q: Question) => void }) {
  const id = `choice-q-${q.id}`;
  return <Press testID={id} onPress={() => onToggle(q)} scaleTo={0.99} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
    accessibilityLabel={`Sawaal ${q.n ?? k + 1}${q.type === "integer" ? ", numerical" : ""}${on ? ", chuna hua" : ""}`} style={[styles.card, on && styles.cardOn]}>
    <View style={styles.head}>
      <Tick on={on} />
      <T testID={`${id}-number`} w="heavy" size={14}>Q {q.n ?? k + 1}</T>
      <View style={styles.kind}><T w="heavy" size={9} color={colors.muted} style={styles.caps}>{q.type === "integer" ? "NUMERICAL" : "MCQ"}</T></View>
    </View>
    {/* The question is only read here: nothing inside it may take the tap from its card. */}
    <View pointerEvents="none" style={styles.stem}>
      {q.text ? <MathText testID={`${id}-text`} text={q.text} size={14.5} backgroundColor={colors.custom_card} /> : null}
      {q.stem.map((p, i) => <StemPicture key={p.url + i} p={p} width={width} testID={`${id}-picture-${i}`} />)}
    </View>
  </Press>;
});
/** What is left of the screen's width inside a question's card, for its pictures. */
export const stemWidth = (screen: number) => Math.max(1, Math.min(screen, 720) - 2 * space.lg - 2 * PAD - 2);

/** The paper so far, subject by subject, with the time each subject brings. */
export function Makeup({ counts, bank, testID }: { counts: Counts; bank: Bank; testID: string }) {
  return <View testID={testID} style={styles.makeup}>
    {SUBJECTS.filter(s => counts[s]).map(s => <View key={s} testID={`${testID}-${s.toLowerCase()}`} style={styles.row}>
      <View style={[styles.dot, { backgroundColor: subjectColor(s) }]} />
      <T w="bold" size={14} style={{ flex: 1 }}>{SHORT[s]}</T>
      <T w="heavy" size={14}>{counts[s]} <T size={12} color={colors.muted}>sawaal</T></T>
      <T w="semibold" size={12.5} color={colors.custom_softText} style={styles.minutes}>{timeLabel(minutesFor({ Physics: 0, Chemistry: 0, Mathematics: 0, [s]: counts[s] }, bank.minutes))}</T>
    </View>)}
    <View style={[styles.row, styles.total]}>
      <T w="heavy" size={14} style={{ flex: 1 }}>Poora paper</T>
      <T testID={`${testID}-total`} w="heavy" size={14}>{totalOf(counts)} <T size={12} color={colors.muted}>sawaal</T></T>
      <T testID={`${testID}-time`} w="heavy" size={12.5} style={styles.minutes}>{timeLabel(minutesFor(counts, bank.minutes))}</T>
    </View>
  </View>;
}

/** The bar at the bottom of a step: what is chosen so far on the left, the way on at the right. */
export function StepBar({ big, small, label, onPress, disabled, testID }: { big: string; small: string; label: string; onPress: () => void; disabled?: boolean; testID: string }) {
  const insets = useSafeAreaInsets();
  return <View testID={testID} style={[styles.bar, { paddingBottom: insets.bottom + 10 }]}>
    <View style={{ flex: 1, minWidth: 0 }}>
      <T testID={`${testID}-count`} w="heavy" size={17} numberOfLines={1}>{big}</T>
      <T testID={`${testID}-note`} size={12} color={colors.muted} numberOfLines={1}>{small}</T>
    </View>
    <Pill testID={`${testID}-go`} label={label} iconRight="arrow-right" disabled={disabled} onPress={onPress} style={disabled ? styles.off : undefined} />
  </View>;
}

const PAD = 14;
const styles = StyleSheet.create({
  tick: { borderWidth: 1.5, borderColor: colors.custom_qFreshLine, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  tickOn: { borderColor: colors.onSurface, backgroundColor: colors.onSurface },
  card: { gap: 10, padding: PAD, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  cardOn: { borderColor: colors.onSurface },
  head: { flexDirection: "row", alignItems: "center", gap: 10 },
  kind: { height: 20, paddingHorizontal: 8, borderRadius: 10, justifyContent: "center", backgroundColor: colors.custom_cardRaised },
  caps: { letterSpacing: 1.2 },
  stem: { gap: 8 },
  makeup: { borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 44 },
  total: { borderTopWidth: 1, borderTopColor: colors.custom_cardLineStrong },
  dot: { width: 8, height: 8, borderRadius: 4 },
  minutes: { width: 86, textAlign: "right" },
  bar: { flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: space.lg, paddingTop: 10, borderTopWidth: 1, borderTopColor: colors.custom_barLine, backgroundColor: colors.custom_bar },
  off: { opacity: 0.4 },
});

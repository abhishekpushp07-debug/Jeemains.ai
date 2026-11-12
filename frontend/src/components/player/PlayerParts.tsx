import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { PaperQuestion, subjectId, subjectOf } from "@/src/assets/paperAssets";
import { colors, radius, space } from "@/src/theme";
import { Press, T } from "../ui";

export type PaletteState = "answered" | "answered_marked" | "marked" | "not_answered" | "fresh";
// NTA-familiar palette: green answered, red not answered, teal marked, grey not visited.
export const PALETTE: Record<PaletteState, { bg: string; fg: string; label: string; line?: string }> = {
  answered: { bg: colors.custom_qAnswered, fg: colors.custom_qInk, label: "Answered" },
  not_answered: { bg: colors.custom_qNotAnswered, fg: colors.custom_qInk, label: "Not answered" },
  fresh: { bg: colors.custom_qFresh, fg: colors.muted, label: "Not visited", line: colors.custom_qFreshLine },
  marked: { bg: colors.custom_qMarked, fg: colors.custom_qInk, label: "Marked for review" },
  answered_marked: { bg: colors.custom_qMarked, fg: colors.custom_qInk, label: "Answered & marked" },
};
export const shortSubject = (s: string) => (s === "Mathematics" ? "Maths" : s);

/** Rounded segmented subject pill, each with answered/total. Scrolls when a paper has many sections. */
export function SubjectSegment({ questions, subject, onSelect, prefix, answered }: {
  questions: PaperQuestion[]; subject: string; onSelect: (s: string) => void; prefix: string; answered: (q: PaperQuestion) => boolean;
}) {
  const subjects = [...new Set(questions.map(subjectOf))];
  const many = subjects.length > 3;
  const items = subjects.map(name => {
    const rows = questions.filter(q => subjectOf(q) === name);
    const done = rows.filter(answered).length;
    const on = name === subject;
    return <Press key={name} testID={`${prefix}-${subjectId(name)}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${name}, ${done} of ${rows.length} answered`}
      onPress={() => onSelect(name)} scaleTo={0.98} style={[styles.seg, many ? styles.segScroll : styles.segFlex, on && { backgroundColor: colors.onSurface }]}>
      <T testID={`${prefix}-${subjectId(name)}-label`} w={on ? "heavy" : "bold"} size={12.5} numberOfLines={1} color={on ? colors.custom_bar : colors.custom_softText}>{shortSubject(name)}</T>
      <T testID={`${prefix}-${subjectId(name)}-count`} w="bold" size={9.5} color={on ? colors.custom_qFreshLine : colors.custom_eyebrow}>{done}/{rows.length}</T>
    </Press>;
  });
  return <View testID={`${prefix}-tabs`} accessibilityRole="tablist" style={styles.segWrap}>
    {many ? <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 2 }}>{items}</ScrollView> : items}
  </View>;
}

/** Round number bubbles; current question gets a white ring. */
export function PaletteGrid({ questions, stateOf, currentId, pendingIds, onSelect, prefix }: {
  questions: PaperQuestion[]; stateOf: (q: PaperQuestion) => PaletteState; currentId?: string; pendingIds: Record<string, unknown>; onSelect: (id: string) => void; prefix: string;
}) {
  return <View testID={`${prefix}-grid`} style={styles.grid}>
    {questions.map(q => {
      const st = stateOf(q), look = PALETTE[st], current = q.id === currentId;
      return <Press key={q.id} testID={`${prefix}-${q.number ?? q.id}`} onPress={() => onSelect(q.id)} haptic={false} scaleTo={0.92}
        accessibilityLabel={`Question ${q.number}, ${look.label}${current ? ", current" : ""}${pendingIds[q.id] ? ", waiting to save" : ""}`} style={[styles.ring, current && styles.ringOn]}>
        <View style={[styles.bubble, { backgroundColor: look.bg, borderColor: look.line ?? look.bg }]}>
          <T w="heavy" size={14} color={look.fg}>{q.number}</T>
        </View>
        {st === "answered_marked" ? <View style={[styles.mini, { backgroundColor: colors.custom_qAnswered }]} /> : null}
        {pendingIds[q.id] ? <View style={[styles.mini, styles.pending]} /> : null}
      </Press>;
    })}
  </View>;
}

export function Legend({ counts, pending }: { counts: Record<PaletteState, number>; pending: number }) {
  const left: PaletteState[] = ["answered", "not_answered", "fresh"], right: PaletteState[] = ["marked", "answered_marked"];
  const row = (k: PaletteState) => <View key={k} testID={`palette-legend-${k}`} style={styles.legendRow}>
    <View style={[styles.legendDot, { backgroundColor: PALETTE[k].bg }]}>{k === "answered_marked" ? <View style={styles.legendMini} /> : null}</View>
    <T size={12} color={colors.custom_softText} style={{ flex: 1 }} numberOfLines={1}>{PALETTE[k].label}</T>
    <T w="heavy" size={12}>{counts[k]}</T>
  </View>;
  return <View testID="palette-legend" style={styles.legend}>
    <View style={styles.legendCol}>{left.map(row)}</View>
    <View style={styles.legendCol}>{right.map(row)}
      {pending ? <View style={styles.legendRow}><View style={[styles.legendDot, { backgroundColor: colors.warning }]} /><T size={12} color={colors.warning} style={{ flex: 1 }}>Waiting to save</T><T w="heavy" size={12} color={colors.warning}>{pending}</T></View> : null}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  segWrap: { flexDirection: "row", padding: 4, gap: 2, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  seg: { minHeight: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", paddingHorizontal: 8, paddingVertical: 2 },
  segFlex: { flex: 1, minWidth: 0 },
  segScroll: { minWidth: 92 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10, justifyContent: "flex-start" },
  ring: { width: 54, height: 54, borderRadius: 27, alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: "transparent" },
  ringOn: { borderColor: colors.onSurface },
  bubble: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  mini: { position: "absolute", top: 3, right: 3, width: 13, height: 13, borderRadius: 7, borderWidth: 2, borderColor: colors.custom_card },
  pending: { top: undefined, bottom: 3, backgroundColor: colors.warning },
  legend: { flexDirection: "row", gap: space.lg, padding: space.md, borderRadius: 16, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine },
  legendCol: { flex: 1, gap: 8, minWidth: 0 },
  legendRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot: { width: 14, height: 14, borderRadius: 7 },
  legendMini: { position: "absolute", top: -3, right: -3, width: 8, height: 8, borderRadius: 4, backgroundColor: colors.custom_qAnswered, borderWidth: 1, borderColor: colors.custom_bar },
});

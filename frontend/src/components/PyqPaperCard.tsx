import React from "react";
import { StyleSheet, View } from "react-native";
import { paperDate, paperState, PyqPaper, resultId } from "@/src/api/pyq";
import { colors, learningTones, space } from "@/src/theme";
import { Button, ErrorBox, Icon, T } from "./ui";
import { LearningBadge, learningStatusTone } from "./LearningTheme";

const STATUS = { new: "Not attempted", active: "In progress", completed: "Completed", grading: "Result preparing", expired: "Time ended", unavailable: "Unavailable" };

export function PyqPaperCard({ paper: p, busy, locked, error, onOpen, onResult }: {
  paper: PyqPaper; busy: boolean; locked: boolean; error?: string; onOpen: () => void; onResult: (id: string) => void;
}) {
  const state = paperState(p);
  const result = resultId(p);
  const active = state === "active";
  const replay = state === "completed" || state === "expired";
  const tone = learningStatusTone(state);
  const label = active ? "Continue" : replay ? "Re-attempt" : "Start";
  const action = active ? "continue" : replay ? "reattempt" : "start";
  return <View testID={`pyq-paper-${p.id}`} style={[styles.card, tone && { borderTopWidth: 4, borderTopColor: learningTones[tone].line }]}>
    <View style={styles.row}>
      <View style={styles.shift}><Icon name="clock-outline" size={13} color={colors.brandText} />
        <T testID={`pyq-shift-${p.id}`} size={11} w="bold" color={colors.brandText}>SHIFT {p.shift}</T>
      </View>
      <LearningBadge testID={`pyq-status-${p.id}`} label={STATUS[state]} tone={tone} />
    </View>
    <T testID={`pyq-paper-title-${p.id}`} size={18} w="heavy" style={styles.title}>{paperDate(p.exam_date)}</T>
    <T testID={`pyq-paper-meta-${p.id}`} size={13} color={colors.muted}>{p.count} questions  ·  {p.minutes ? `${p.minutes} min` : "Untimed"}  ·  {p.maximum} marks</T>
    <View style={styles.rule}>
      <Icon name="book-check-outline" size={15} color={colors.brandText} />
      <T testID={`pyq-paper-solutions-${p.id}`} size={12} color={colors.muted} style={styles.ruleText}>Answers & available solutions after submit</T>
    </View>
    {p.attempt_count > 0 ? <T testID={`pyq-attempt-count-${p.id}`} size={11} color={colors.mutedSecondary}>{p.attempt_count} {p.attempt_count === 1 ? "attempt" : "attempts"} · previous results stay saved</T> : null}
    {state === "grading" ? <T testID={`pyq-awaiting-result-${p.id}`} color={colors.muted} size={12}>Your attempt is saved. Refresh shortly for the released result.</T> : null}
    <ErrorBox testID={`pyq-start-error-${p.id}`} error={error} />
    <View style={styles.actions}>
      {result ? <Button testID={`pyq-result-button-${p.id}`} label="Result" icon="chart-box-outline" kind="secondary" disabled={locked} style={styles.button} onPress={() => onResult(result)} /> : null}
      {state !== "grading" && state !== "unavailable" ? <Button testID={`pyq-${action}-button-${p.id}`} label={label} icon={active ? "play" : replay ? undefined : "arrow-right"}
        busy={busy} disabled={locked && !busy} color={colors.brandPrimary} onPress={onOpen} style={styles.button} /> : null}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 20, backgroundColor: colors.surfaceSecondary, borderRadius: 16, borderWidth: 1, borderColor: colors.border, gap: space.sm },
  title: { marginTop: space.md, marginBottom: space.xs, letterSpacing: 0 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm },
  shift: { flexDirection: "row", alignItems: "center", gap: 5, backgroundColor: colors.brandTertiary, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  rule: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 6, marginTop: 2 },
  ruleText: { flex: 1 },
  actions: { flexDirection: "row", flexWrap: "wrap", gap: space.sm, marginTop: space.xl },
  button: { flex: 1, paddingHorizontal: space.sm },
});
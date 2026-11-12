import React from "react";
import { StyleSheet, View } from "react-native";
import { paperDate, paperState, PyqPaper, resultId } from "@/src/api/pyq";
import { colors, space } from "@/src/theme";
import { ErrorBox, Icon, T } from "./ui";
import { DCard, Pill, StatusLine } from "./design";
import { learningStatusTone } from "./LearningTheme";

const STATUS = { new: "Not attempted", active: "In progress", completed: "Completed", grading: "Result preparing", expired: "Time ended", unavailable: "Unavailable" };
export const toneInk = (tone?: string) => tone === "active" ? colors.custom_timerAmber : tone === "completed" ? colors.custom_mint : tone === "saved" ? colors.custom_savedBlue : tone === "error" ? colors.error : colors.custom_eyebrow;

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
  return <DCard testID={`pyq-paper-${p.id}`} style={styles.card}>
    <View style={styles.row}>
      <View style={styles.shift}><Icon name="clock-outline" size={12} color={colors.brandText} />
        <T testID={`pyq-shift-${p.id}`} size={10} w="heavy" color={colors.brandText} style={{ letterSpacing: 1.4 }}>SHIFT {p.shift}</T>
      </View>
      <StatusLine testID={`pyq-status-${p.id}`} label={STATUS[state]} color={toneInk(tone)} />
    </View>
    <T testID={`pyq-paper-title-${p.id}`} size={18} w="heavy">{paperDate(p.exam_date)}</T>
    <T testID={`pyq-paper-meta-${p.id}`} size={12.5} color={colors.muted}>{p.count} questions  ·  {p.minutes ? `${p.minutes} min` : "Untimed"}  ·  {p.maximum} marks</T>
    <T testID={`pyq-paper-solutions-${p.id}`} size={11.5} color={colors.custom_eyebrow}>Answers & available solutions after submit</T>
    {p.attempt_count > 0 ? <T testID={`pyq-attempt-count-${p.id}`} size={11} color={colors.custom_eyebrow}>{p.attempt_count} {p.attempt_count === 1 ? "attempt" : "attempts"} · previous results stay saved</T> : null}
    {state === "grading" ? <T testID={`pyq-awaiting-result-${p.id}`} color={colors.muted} size={12}>Your attempt is saved. Refresh shortly for the released result.</T> : null}
    <ErrorBox testID={`pyq-start-error-${p.id}`} error={error} />
    <View style={styles.actions}>
      {result ? <Pill testID={`pyq-result-button-${p.id}`} label="Result" icon="chart-box-outline" kind="outline" size="sm" disabled={locked} onPress={() => onResult(result)} /> : null}
      {state !== "grading" && state !== "unavailable" ? <Pill testID={`pyq-${action}-button-${p.id}`} label={label} iconRight={active ? "play" : "arrow-right"} size="sm"
        kind={active ? "brand" : "light"} busy={busy} disabled={locked && !busy} onPress={onOpen} /> : null}
    </View>
  </DCard>;
}

const styles = StyleSheet.create({
  card: { padding: 18, gap: 6 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: space.sm, marginBottom: 4 },
  shift: { flexDirection: "row", alignItems: "center", gap: 5, backgroundColor: colors.brandTertiary, paddingHorizontal: 10, height: 24, borderRadius: 12 },
  actions: { flexDirection: "row", flexWrap: "wrap", justifyContent: "flex-end", gap: space.sm, marginTop: space.md },
});

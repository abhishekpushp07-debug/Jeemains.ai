import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { An, Q, mmss, pc } from "./format";
import { TagChip } from "./parts";

/** Above a solution: the student's time on this question against Par and against the class. */
export function SolutionInsight({ q, copy }: { q?: Q; copy: An["copy"] }) {
  if (!q) return null;
  const c = q.class;
  const facts: [string, string][] = [];
  if (q.time != null) facts.push(["time", `Aapka time ${mmss(q.time)}`]);
  if (q.par != null) facts.push(["par", `Par ${mmss(q.par)}${q.par_source === "solvers" ? ` (${q.par_n} solvers se)` : ""}`]);
  if (c) facts.push(["class", `${pc(c.correct)} ne sahi kiya`]);
  if (c?.topper_time > 0) facts.push(["topper", `Topper ${mmss(c.topper_time)}`]);
  if (c?.top_wrong) facts.push(["wrong", `Sabse zyada galti: option ${c.top_wrong.option} (${c.top_wrong.percent}%)`]);
  if (q.visits > 1) facts.push(["visits", `${q.visits} baar dekha`]);
  if (q.changed) facts.push(["changed", `Jawab badla ${q.changed}`]);
  return <View testID="solution-insight-line" style={styles.line}>
    <View style={styles.head}>
      <T size={11.5} w="bold" color={colors.custom_softText} numberOfLines={1} style={{ flexShrink: 1 }}>{q.subject} · {copy.levels[q.difficulty] || "—"}</T>
      {q.tag ? <TagChip tag={q.tag} copy={copy} /> : null}
    </View>
    {facts.length ? <View style={styles.facts}>
      {facts.map(([k, text]) => <View key={k} testID={"solution-insight-" + k} style={styles.fact}><T size={11.5} w="bold" color={colors.custom_softText}>{text}</T></View>)}
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  line: { gap: 8, padding: space.md, borderRadius: 14, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine },
  head: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  facts: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  fact: { minHeight: 24, paddingHorizontal: 9, borderRadius: 12, justifyContent: "center", backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
});

import React, { useMemo, useState } from "react";
import { FlatList, ScrollView, StyleSheet, View } from "react-native";
import { PaperQuestion, subjectId, subjectOf } from "@/src/assets/paperAssets";
import { colors, foregroundOn, radius, space, subjectColor } from "@/src/theme";
import { Icon, IconName, Press, T } from "../ui";

export function useSubjectNavigation<T extends PaperQuestion>(questions: T[]) {
  const [chosen, setChosen] = useState("");
  const [remembered, setRemembered] = useState<Record<string, string>>({});
  const subjects = useMemo(() => [...new Set(questions.map(subjectOf))], [questions]);
  const question = questions.find(q => q.id === chosen) || questions[0];
  const subject = question ? subjectOf(question) : "";
  const rows = useMemo(() => questions.filter(q => subjectOf(q) === subject), [questions, subject]);
  const index = rows.findIndex(q => q.id === question?.id);
  function select(qid: string) {
    const q = questions.find(q => q.id === qid);
    if (!q) return;
    setChosen(qid); setRemembered(old => ({ ...old, [subjectOf(q)]: qid }));
  }
  function selectSubject(name: string) {
    const row = questions.find(q => q.id === remembered[name] && subjectOf(q) === name) || questions.find(q => subjectOf(q) === name);
    if (row) select(row.id);
  }
  return { subjects, question, subject, rows, index, select, selectSubject };
}

export function SubjectTabs({ questions, subject, onSelect, prefix }: { questions: PaperQuestion[]; subject: string; onSelect: (subject: string) => void; prefix: string }) {
  const subjects = [...new Set(questions.map(subjectOf))];
  return <ScrollView testID={`${prefix}-tabs`} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs}>
    {subjects.map(name => {
      const active = name === subject, color = subjectColor(name);
      return <Press testID={`${prefix}-${subjectId(name)}`} key={name} accessibilityRole="tab" accessibilityState={{ selected: active }} accessibilityLabel={`${name}, ${questions.filter(q => subjectOf(q) === name).length} questions`} onPress={() => onSelect(name)} style={[styles.tab, { backgroundColor: active ? color : colors.surfaceSecondary, borderColor: active ? color : colors.border }]}>
        <T testID={`${prefix}-${subjectId(name)}-label`} w="bold" size={13} color={active ? foregroundOn(color) : colors.onSurface}>{name}</T>
        <T testID={`${prefix}-${subjectId(name)}-count`} size={11} w="bold" color={active ? foregroundOn(color) : colors.muted}>{questions.filter(q => subjectOf(q) === name).length}</T>
      </Press>;
    })}
  </ScrollView>;
}

export type QuestionAppearance = { bg: string; fg: string; label: string; icon?: IconName };
export const gridColumns = (width: number) => Math.max(1, Math.min(6, Math.floor((width + 8) / 52)));
export function QuestionGrid({ questions, onSelect, appearance, prefix }: { questions: PaperQuestion[]; onSelect: (id: string) => void; appearance: (q: any) => QuestionAppearance; prefix: string }) {
  const [width, setWidth] = useState(224);
  const columns = gridColumns(width);
  return <View testID={`${prefix}-grid`} onLayout={e => setWidth(e.nativeEvent.layout.width)} style={styles.grid}>
    <FlatList key={columns} data={questions} numColumns={columns} keyExtractor={q => q.id} style={styles.list} columnWrapperStyle={columns > 1 ? styles.row : undefined} contentContainerStyle={styles.listContent}
      renderItem={({ item }) => { const state = appearance(item); return <Press testID={`${prefix}-${item.number ?? item.id}`} onPress={() => onSelect(item.id)} accessibilityLabel={`Question ${item.number}, ${subjectOf(item)}, ${state.label}`} style={[styles.cell, { backgroundColor: state.bg }]}>
        <T w="heavy" size={14} color={state.fg}>{item.number}</T>{state.icon ? <Icon name={state.icon} size={10} color={state.fg} style={styles.state} /> : null}
      </Press>; }} />
  </View>;
}
const styles = StyleSheet.create({
  tabs: { gap: space.sm, paddingVertical: 2 }, tab: { flexDirection: "row", alignItems: "center", justifyContent: "center", minHeight: 44, gap: 8, paddingHorizontal: space.md, borderRadius: radius.md, borderWidth: 1 },
  grid: { width: "100%", flexShrink: 1 }, list: { maxHeight: 300 }, listContent: { gap: 8, paddingBottom: 4 }, row: { gap: 8 },
  cell: { width: 44, height: 44, borderRadius: 10, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: colors.borderStrong }, state: { position: "absolute", top: 3, right: 3 },
});
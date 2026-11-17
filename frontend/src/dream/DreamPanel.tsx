// The Rank tab's Dream College tool (its own dark violet tile): the exam switch (JEE Main / BITSAT / COMEDK with N/5)
// and the Dream College Meter for that exam, with remove buttons. Opens on the first exam that has dreams.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { space } from "@/src/theme";
import { Switch } from "@/src/rank/controls";
import { DreamMeter } from "./DreamMeter";
import { DreamExam, dreamsOf, EXAM_NAME, EXAMS, MAX_DREAMS, useDreams } from "./store";

export function DreamPanel({ onAdd }: { onAdd: () => void }) {
  const s = useDreams();
  const [exam, setExam] = useState<DreamExam | null>(null);
  const first = EXAMS.find(e => dreamsOf(s, e).length) ?? null;
  // Until the student picks an exam, follow the first exam that has dreams (they load from the phone after mount).
  useEffect(() => { if (exam === null && first) setExam(first); }, [exam, first]);
  const shown = exam ?? first ?? "jee";
  return <View testID="dream-panel" style={styles.wrap}>
    <Switch prefix="dream-exam" value={shown} onChange={setExam}
      items={EXAMS.map(e => ({ key: e, label: `${EXAM_NAME[e]} ${dreamsOf(s, e).length}/${MAX_DREAMS}` }))} />
    <DreamMeter exam={shown} testID="dream-meter" editable onAdd={onAdd} />
  </View>;
}

const styles = StyleSheet.create({ wrap: { gap: space.md } });

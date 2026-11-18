// Home's Dream College Meter: the exam of the latest mock (else the first exam with dreams), its first 3 dreams,
// and links into the Rank tab to add more or see all. With dreams in more than one exam, a switch shows each of them.
import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { space } from "@/src/theme";
import { Switch } from "@/src/rank/controls";
import { DreamMeter } from "./DreamMeter";
import { DreamExam, dreamsOf, EXAM_NAME, EXAMS, MAX_DREAMS, useDreams } from "./store";

export function HomeDream() {
  const s = useDreams();
  const router = useRouter();
  const [picked, setPicked] = useState<DreamExam | null>(null);
  const withDreams = EXAMS.filter(e => dreamsOf(s, e).length);
  const auto: DreamExam = s.mocks[0]?.exam ?? withDreams[0] ?? "jee";
  const exam = picked && (withDreams.includes(picked) || picked === auto) ? picked : auto;
  const go = (tool: "college" | "dream") => router.push({ pathname: "/(tabs)/rank", params: { tool, at: String(Date.now()) } });
  return <View style={styles.wrap}>
    {withDreams.length > 1 ? <Switch prefix="home-dream-exam" value={exam} onChange={setPicked}
      items={withDreams.map(e => ({ key: e, label: `${EXAM_NAME[e]} ${dreamsOf(s, e).length}/${MAX_DREAMS}` }))} /> : null}
    <DreamMeter exam={exam} testID="home-dream" limit={3} onAdd={() => go("college")} onMore={() => go("dream")} />
  </View>;
}

const styles = StyleSheet.create({ wrap: { gap: space.sm } });

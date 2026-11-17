// Home's Dream College Meter: the exam of the latest mock (else the first exam with dreams), its first 3 dreams,
// and links into the Rank tab to add more or see all.
import React from "react";
import { useRouter } from "expo-router";
import { DreamMeter } from "./DreamMeter";
import { DreamExam, dreamsOf, EXAMS, useDreams } from "./store";

export function HomeDream() {
  const s = useDreams();
  const router = useRouter();
  const exam: DreamExam = s.mocks[0]?.exam ?? EXAMS.find(e => dreamsOf(s, e).length) ?? "jee";
  const go = (tool: "college" | "dream") => router.push({ pathname: "/(tabs)/rank", params: { tool, at: String(Date.now()) } });
  return <DreamMeter exam={exam} testID="home-dream" limit={3} onAdd={() => go("college")} onMore={() => go("dream")} />;
}

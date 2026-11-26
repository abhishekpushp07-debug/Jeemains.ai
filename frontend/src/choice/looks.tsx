// Student Choice's colour: the top of each screen is a dark-red card like the result page's "Aapka Score" card (gloss,
// a glass glint from corner to corner, rose / gold / blush running round its edge), and the subjects are glossy tabs
// in their own colours (Physics red, Chemistry amber, Maths teal), built like My Tests' tabs. The cards below stay white.
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Shine } from "@/src/analysis/Shine";
import { GlossTabs, TabLook } from "@/src/components/GlossTabs";
import { colors, tabEdges, toolEdges } from "@/src/theme";
import { SHORT, Subject } from "./api";

export const SUBJECT_LOOK: Record<Subject, TabLook> = {
  Physics: { on: [colors.custom_tabRed, colors.custom_tabRedDeep], rest: [colors.custom_tabRedSoft, colors.custom_tabRedSoftDeep], edge: tabEdges.red, glow: colors.custom_tabRedGlow },
  Chemistry: { on: [colors.custom_tabAmber, colors.custom_tabAmberDeep], rest: [colors.custom_tabAmberSoft, colors.custom_tabAmberSoftDeep], edge: tabEdges.amber, glow: colors.custom_tabAmberGlow },
  Mathematics: { on: [colors.custom_tabTeal, colors.custom_tabTealDeep], rest: [colors.custom_tabTealSoft, colors.custom_tabTealSoftDeep], edge: tabEdges.teal, glow: colors.custom_tabTealGlow },
};
/** The soft wash a chosen chapter of this subject wears. */
export const subjectWash = (s: Subject) => (s === "Physics" ? colors.custom_washPhysics : s === "Chemistry" ? colors.custom_washChemistry : colors.custom_washMaths);

const key = (s: Subject) => s.toLowerCase() as Lowercase<Subject>;
/** The subjects as glossy tabs. testIDs stay `<prefix>-physics` and `<prefix>-physics-count`, as the pills had. */
export function SubjectTabs({ prefix, value, onChange, items }: { prefix: string; value: Subject; onChange: (s: Subject) => void; items: { subject: Subject; count: number }[] }) {
  return <GlossTabs prefix={prefix} value={key(value)} onChange={k => onChange(items.find(i => key(i.subject) === k)!.subject)}
    items={items.map(i => ({ key: key(i.subject), label: SHORT[i.subject], look: SUBJECT_LOOK[i.subject], sub: String(i.count), subTestID: `${prefix}-${key(i.subject)}-count` }))} />;
}

/** The dark-red card at the top of a Student Choice screen. Words on it are white (`ON_HERO`). */
export function ChoiceHero({ testID, children }: { testID: string; children: React.ReactNode }) {
  return <View testID={testID}>
    <Shine radius={24} ring={3} edge={toolEdges.maroon} gloss={colors.custom_fireGloss} glint={colors.custom_fireGlint} band={84} part={46} corner face={styles.hero}
      backdrop={<LinearGradient pointerEvents="none" colors={[colors.brandSecondary, colors.custom_series]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}>
      {children}
    </Shine>
  </View>;
}
export const ON_HERO = { ink: colors.onSurfaceInverse, soft: colors.custom_whiteA70 };

export const heroStyles = StyleSheet.create({
  kicker: { letterSpacing: 1.4 },
  // Clear glass on the red, as the Misfire card's chips.
  glass: { borderRadius: 999, paddingHorizontal: 11, height: 28, justifyContent: "center", backgroundColor: colors.custom_fireGlass, borderWidth: 1, borderColor: colors.custom_fireLine },
  counts: { flexDirection: "row", borderRadius: 16, backgroundColor: colors.custom_whiteA15 },
  count: { flex: 1, minHeight: 58, alignItems: "center", justifyContent: "center", paddingVertical: 8, paddingHorizontal: 2 },
  countLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_whiteA15 },
});

const styles = StyleSheet.create({
  hero: { gap: 12, padding: 18 },
});

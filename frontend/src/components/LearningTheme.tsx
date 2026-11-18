import React from "react";
import { StyleSheet, View } from "react-native";
import { colors, LearningTone, learningTones, space } from "@/src/theme";
import { Icon, IconName, Press, T } from "./ui";

export function learningStatusTone(status: string): LearningTone | undefined {
  if (["active", "progress", "grading", "expired"].includes(status)) return "active";
  if (status === "completed") return "completed";
  if (status === "saved") return "saved";
  if (status === "unavailable") return "error";
  return undefined;
}

export function LearningTab({ label, icon, active, onPress, testID }: {
  label: string; tone: LearningTone; icon: IconName; active: boolean; onPress: () => void; testID: string;
}) {
  const ink = active ? colors.custom_bar : colors.custom_softText;
  return <Press testID={testID} accessibilityRole="tab" accessibilityState={{ selected: active }} onPress={onPress} scaleTo={0.98}
    style={[styles.tab, active && { backgroundColor: colors.onSurface, borderColor: colors.onSurface }]}>
    <Icon name={icon} size={16} color={ink} />
    <T testID={`${testID}-label`} size={13} w={active ? "heavy" : "bold"} color={ink}>{label}</T>
  </Press>;
}

export function LearningStat({ label, value, tone, testID }: { label: string; value: string | number; tone?: LearningTone; testID: string }) {
  return <View testID={testID} style={styles.stat}>
    {tone ? <View style={[styles.dot, { backgroundColor: learningTones[tone].ink }]} /> : null}
    <T testID={`${testID}-value`} size={22} w="heavy" color={tone ? learningTones[tone].ink : colors.onSurface}>{value}</T>
    <T testID={`${testID}-label`} size={12} color={colors.custom_eyebrow}>{label}</T>
  </View>;
}

const styles = StyleSheet.create({
  tab: { minHeight: 44, paddingHorizontal: space.lg, borderRadius: 999, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", gap: 6 },
  stat: { flex: 1, minWidth: 0, padding: space.md, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, gap: 2 },
  dot: { position: "absolute", top: space.md, right: space.md, width: 7, height: 7, borderRadius: 4 },
});
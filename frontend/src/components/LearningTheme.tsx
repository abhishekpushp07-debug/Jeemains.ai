import React from "react";
import { StyleSheet, View } from "react-native";
import { academicStyles, colors, LearningTone, learningTones, space } from "@/src/theme";
import { Icon, IconName, Press, T } from "./ui";

export function learningStatusTone(status: string): LearningTone | undefined {
  if (["active", "progress", "grading", "expired"].includes(status)) return "active";
  if (status === "completed") return "completed";
  if (status === "saved") return "saved";
  if (status === "unavailable") return "error";
  return undefined;
}

export function LearningBadge({ label, tone, testID }: { label: string; tone?: LearningTone; testID: string }) {
  const palette = tone ? learningTones[tone] : { soft: colors.surface, ink: colors.muted };
  return <View testID={testID} style={[styles.badge, { backgroundColor: palette.soft }]}>
    <T testID={`${testID}-label`} size={11} w="bold" color={palette.ink}>{label}</T>
  </View>;
}

export function LearningTab({ label, icon, active, onPress, testID }: {
  label: string; tone: LearningTone; icon: IconName; active: boolean; onPress: () => void; testID: string;
}) {
  const state = active ? academicStyles.selectedTab : academicStyles.tab;
  const ink = state.color;
  return <Press testID={testID} accessibilityRole="tab" accessibilityState={{ selected: active }} onPress={onPress}
    style={[styles.tab, { backgroundColor: state.backgroundColor, borderBottomColor: state.borderTopColor }]}>
    <Icon name={icon} size={16} color={ink} />
    <T testID={`${testID}-label`} size={13} w="bold" color={ink}>{label}</T>
  </Press>;
}

export function LearningStat({ label, value, tone, testID }: { label: string; value: string | number; tone?: LearningTone; testID: string }) {
  return <View testID={testID} style={[styles.stat, { borderTopColor: tone ? learningTones[tone].line : colors.border }]}>
    <T testID={`${testID}-value`} size={22} w="heavy">{value}</T>
    <T testID={`${testID}-label`} size={12} color={colors.muted}>{label}</T>
  </View>;
}

const styles = StyleSheet.create({
  badge: { alignSelf: "flex-start", borderRadius: 6, paddingHorizontal: 7, paddingVertical: 4, flexShrink: 1 },
  tab: { minHeight: 50, paddingHorizontal: space.md, paddingVertical: space.sm, borderRadius: 9, borderBottomWidth: 3, flexDirection: "row", alignItems: "center", gap: 6 },
  stat: { flex: 1, minWidth: 0, padding: space.md, borderRadius: 12, borderWidth: 1, borderColor: colors.border, borderTopWidth: 4, backgroundColor: colors.surfaceSecondary, gap: space.xs },
});
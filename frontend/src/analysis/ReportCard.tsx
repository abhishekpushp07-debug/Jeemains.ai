// The analysis report as one deep-teal card at the top of every section, about an inch high.
// One tap gives the same PDF, the same way, as the old "Report download" button. Nothing on it moves.
import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, Press, T } from "@/src/components/ui";
import { colors } from "@/src/theme";

export function ReportCard({ busy, disabled, narrow, onPress }: { busy: boolean; disabled: boolean; narrow: boolean; onPress: () => void }) {
  return <Press testID="a2-download-report" onPress={onPress} disabled={disabled} scaleTo={0.985} accessibilityLabel="Report download. Poora analysis ek PDF mein" accessibilityState={{ busy }} style={styles.wrap}>
    <LinearGradient colors={[colors.custom_reportFrom, colors.custom_reportMid, colors.custom_reportTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.card, narrow && styles.cardNarrow]}>
      <View pointerEvents="none" style={styles.ringTop} />
      <View pointerEvents="none" style={styles.ringFoot} />
      <View style={[styles.badge, narrow && styles.badgeNarrow]}><Icon name="file-pdf-box" size={narrow ? 26 : 32} color={colors.custom_reportInk} /></View>
      <View style={styles.words}>
        <T testID="a2-download-report-title" w="heavy" size={narrow ? 19 : 22} color={colors.custom_reportInk} numberOfLines={2} style={styles.title}>Report download</T>
        <T testID="a2-download-report-sub" w="semibold" size={13.5} color={colors.custom_reportInkSoft} numberOfLines={2}>Poora analysis ek PDF mein</T>
      </View>
      <View style={styles.go}>
        {busy ? <ActivityIndicator size="small" color={colors.custom_reportTo} /> : <Icon name="tray-arrow-down" size={22} color={colors.custom_reportTo} />}
      </View>
    </LinearGradient>
  </Press>;
}

const styles = StyleSheet.create({
  wrap: { borderRadius: 22, overflow: "hidden" },
  // 152 points is about one inch on a phone (an inch is 153 to 160 points).
  card: { minHeight: 152, flexDirection: "row", alignItems: "center", gap: 14, paddingHorizontal: 20, paddingVertical: 20, borderRadius: 22, overflow: "hidden" },
  cardNarrow: { gap: 10, paddingHorizontal: 14 },
  ringTop: { position: "absolute", width: 190, height: 190, borderRadius: 95, right: -60, top: -84, backgroundColor: colors.custom_reportGlow },
  ringFoot: { position: "absolute", width: 130, height: 130, borderRadius: 65, right: 54, bottom: -84, backgroundColor: colors.custom_reportGlow },
  badge: { width: 60, height: 60, borderRadius: 18, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reportGlass, borderWidth: 1, borderColor: colors.custom_reportLine },
  badgeNarrow: { width: 48, height: 48, borderRadius: 15 },
  words: { flex: 1, minWidth: 0, gap: 3 },
  title: { letterSpacing: -0.5 },
  go: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reportInk },
});

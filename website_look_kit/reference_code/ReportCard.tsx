// The analysis report as one light sky-blue and teal card at the top of every section, about an inch high, with dark words.
// One tap gives the same PDF, the same way, as the old "Report download" button.
// Glossy glass: five colours run round its edge, a glint crosses it on the diagonal and three stars twinkle on the edge.
import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { colors } from "@/src/theme";
import { Shine } from "./Shine";

const TONES = [colors.custom_reportSky, colors.custom_reportAqua] as const;

export function ReportCard({ busy, disabled, narrow, rest, onPress }: { busy: boolean; disabled: boolean; narrow: boolean; rest: boolean; onPress: () => void }) {
  return <Press testID="a2-download-report" onPress={onPress} disabled={disabled} scaleTo={0.985} accessibilityLabel="Report download. Poora analysis ek PDF mein" accessibilityState={{ busy }} style={[styles.wrap, disabled && styles.flat]}>
    <Shine radius={22} ring={3} tones={TONES} gloss={colors.custom_reportGloss} glint={colors.custom_reportGlint} band={72} part={46} sparkles={3} rest={rest} face={[styles.card, narrow && styles.cardNarrow]}>
      <View pointerEvents="none" style={styles.ringTop} />
      <View pointerEvents="none" style={styles.ringFoot} />
      <View style={[styles.badge, narrow && styles.badgeNarrow]}><Icon name="file-pdf-box" size={narrow ? 26 : 32} color={colors.custom_reportInk} /></View>
      <View style={styles.words}>
        <T testID="a2-download-report-title" w="heavy" size={narrow ? 19 : 22} color={colors.custom_reportInk} numberOfLines={2} style={styles.title}>Report download</T>
        <T testID="a2-download-report-sub" w="semibold" size={13.5} color={colors.custom_reportInkSoft} numberOfLines={2}>Poora analysis ek PDF mein</T>
      </View>
      <View style={styles.go}>
        {busy ? <ActivityIndicator size="small" color={colors.custom_reportOnInk} /> : <Icon name="tray-arrow-down" size={22} color={colors.custom_reportOnInk} />}
      </View>
    </Shine>
  </Press>;
}

const styles = StyleSheet.create({
  // The soft sky glow under the card; the solid colour behind the edge lets Android draw it too.
  wrap: { borderRadius: 22, backgroundColor: colors.custom_reportSky, shadowColor: colors.custom_reportHalo, shadowOpacity: 0.34, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 8 },
  // While the file is being made the card is half faded; Android would show its own shadow through it.
  flat: { elevation: 0 },
  // 152 points is about one inch on a phone (an inch is 153 to 160 points): 146 for the face and 3 for the edge on each side.
  card: { minHeight: 146, flexDirection: "row", alignItems: "center", gap: 14, paddingHorizontal: 17, paddingVertical: 17 },
  cardNarrow: { gap: 10, paddingHorizontal: 11 },
  ringTop: { position: "absolute", width: 190, height: 190, borderRadius: 95, right: -60, top: -84, backgroundColor: colors.custom_reportGlow },
  ringFoot: { position: "absolute", width: 130, height: 130, borderRadius: 65, right: 54, bottom: -84, backgroundColor: colors.custom_reportGlow },
  badge: { width: 60, height: 60, borderRadius: 18, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reportGlass, borderWidth: 1, borderColor: colors.custom_reportLine },
  badgeNarrow: { width: 48, height: 48, borderRadius: 15 },
  words: { flex: 1, minWidth: 0, gap: 3 },
  title: { letterSpacing: -0.5 },
  go: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_reportInk },
});

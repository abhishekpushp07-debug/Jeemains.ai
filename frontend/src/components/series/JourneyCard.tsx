import React from "react";
import { StyleSheet, View } from "react-native";
import { ErrorBox, Icon, IconName, Skeleton, T } from "@/src/components/ui";
import { DCard, ProgressRing } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { DayInfo, Streak, skippedCount } from "@/src/series";
import { istDate } from "@/src/navigation";

function Fact({ icon, color, bg, value, label, testID }: { icon: IconName; color: string; bg: string; value: string; label: string; testID: string }) {
  return <View testID={testID} style={styles.fact}>
    <View style={[styles.factIcon, { backgroundColor: bg }]}><Icon name={icon} size={15} color={color} /></View>
    <View style={{ flex: 1 }}>
      <T w="heavy" size={14} numberOfLines={1}>{value}</T>
      <T size={10.5} color={colors.custom_eyebrow}>{label}</T>
    </View>
  </View>;
}

export function JourneyCard({ streak, days, error, retry }: { streak: Streak | null; days: DayInfo[]; error?: string; retry: () => void }) {
  if (error && !streak) return <ErrorBox error="Your streak couldn’t load. Your submissions are safe." retry={retry} testID="streak-error" />;
  if (!streak) return <Skeleton h={208} style={{ borderRadius: 24 }} />;
  const done = streak.completed_count;
  const cups = streak.milestones || [];
  const total = streak.total_days || Math.max(1, ...cups.map(c => c.days)); // the website's day count
  return <DCard testID="streak-card" style={styles.card}>
    <View style={styles.row}>
      <ProgressRing testID="streak-done" size={108} stroke={9} value={done / total} track={colors.custom_qFresh} gradient={[colors.custom_qMarked, colors.custom_doneInk]} label={`${done} of ${total} days`}>
        <T w="heavy" size={24}>{done}</T>
        <T w="bold" size={10} color={colors.custom_eyebrow}>/{total} days</T>
      </ProgressRing>
      <View style={{ flex: 1, gap: space.md }}>
        <Fact testID="streak-current" icon="fire" color={colors.custom_flame} bg={colors.custom_flameSoft} value={`${streak.current_streak}-day streak`} label="current" />
        <Fact testID="streak-best" icon="star" color={colors.custom_gold} bg={colors.custom_goldSoft} value={`Best ${streak.best_streak}`} label="longest run" />
        <Fact testID="streak-skipped" icon="cancel" color={colors.custom_missInk} bg={colors.custom_missSoft} value={`${skippedCount(days)} skipped`} label="days missed" />
      </View>
    </View>
    {streak.stage === "prelaunch" ? <T size={11.5} color={colors.custom_eyebrow}>{streak.first_date ? `Starts ${istDate(streak.first_date)}. ` : ""}No early points, no pretend progress.</T> : null}
    <View style={styles.track} accessibilityLabel={`Cups: ${cups.filter(c => c.earned).length} of ${cups.length} earned`}>
      <View style={styles.line} />
      <View style={[styles.lineFill, { width: `${Math.min(100, (streak.best_streak / total) * 100)}%` }]} />
      {cups.map(c => <View key={c.days} testID={"streak-cup-" + c.days} accessibilityLabel={`${c.title} cup, ${c.days} days, ${c.earned ? "earned" : "locked"}`}
        style={[styles.cup, { left: `${Math.min(100, (c.days / total) * 100)}%` }]}>
        <View style={[styles.cupDot, c.earned ? styles.cupOn : styles.cupOff]}>
          <Icon name={c.earned ? "trophy" : "lock"} size={11} color={c.earned ? colors.onSurfaceInverse : colors.muted} />
        </View>
        <T w="bold" size={9.5} color={c.earned ? colors.custom_gold : colors.custom_eyebrow}>{c.days}d</T>
      </View>)}
    </View>
  </DCard>;
}

const styles = StyleSheet.create({
  card: { borderRadius: 24, gap: space.lg, padding: 20 },
  row: { flexDirection: "row", alignItems: "center", gap: space.lg },
  fact: { flexDirection: "row", alignItems: "center", gap: space.sm },
  factIcon: { width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center" },
  track: { height: 44, marginHorizontal: 11, marginTop: space.xs },
  line: { position: "absolute", left: 0, right: 0, top: 9, height: 4, borderRadius: 2, backgroundColor: colors.custom_qFresh },
  lineFill: { position: "absolute", left: 0, top: 9, height: 4, borderRadius: 2, backgroundColor: colors.custom_doneInk },
  cup: { position: "absolute", top: 0, width: 30, marginLeft: -15, alignItems: "center", gap: 4 },
  cupDot: { width: 22, height: 22, borderRadius: 11, alignItems: "center", justifyContent: "center", borderWidth: 1 },
  cupOn: { backgroundColor: colors.custom_gold, borderColor: colors.custom_gold },
  cupOff: { backgroundColor: colors.custom_cardRaised, borderColor: colors.custom_qFreshLine },
});

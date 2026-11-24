// AITS Analysis: every All India day the student has attempted, newest first, each with its score and a blood-red
// "Analysis" button that opens that day's analysis. Reached from the series page; back from a day's analysis lands here,
// and back again reaches the series page.
import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { Empty, ErrorBox, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, ScreenHeader } from "@/src/components/design";
import { AnalysisButton } from "@/src/components/series/AnalysisButton";
import { colors, space } from "@/src/theme";
import { istDate } from "@/src/navigation";
import { DayInfo, dayAttempt, istTime, useSeriesData } from "@/src/series";

export default function SeriesAnalysis() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { series, history, days } = useSeriesData(user?.id);
  const attempted = days.filter(d => !!dayAttempt(d)).sort((a, b) => b.day - a.day);
  const loading = !series.data || (!history.data && !history.error);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/live"));

  return (
    <View testID="series-analysis-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="series-analysis-header" title="AITS Analysis" eyebrow="All India Series · har attempt" backTestID="series-analysis-back" onBack={back} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.md }}>
        <ErrorBox error={history.error && !history.data ? history.error : ""} retry={history.reload} testID="series-analysis-error" />
        {!loading && attempted.some(d => !!dayAttempt(d)?.summary) ? <Pill testID="series-analysis-misfire" kind="outline" size="sm" icon="crosshairs" label="AITS ki galtiyan dobara solve karo" onPress={() => router.push("/misfire?tab=aits" as any)} /> : null}
        {loading ? <><Skeleton h={150} style={{ borderRadius: 20 }} /><Skeleton h={150} style={{ borderRadius: 20 }} /></>
          : attempted.length === 0 ? <DCard testID="series-analysis-empty"><Empty icon="chart-donut" title="Abhi koi AITS attempt nahi." body="Kisi live din ka paper do. Submit hote hi wo yahan apni analysis ke saath aa jayega." /></DCard>
          : attempted.map((d, i) => <Row key={d.day} day={d} testID={`series-analysis-${i}`} onAnalysis={id => router.push(`/result/${id}` as any)} onResume={id => router.push(`/attempt/${id}` as any)} />)}
      </ScrollView>
    </View>
  );
}

/** One attempted day: four facts (day, date, score, status) and the action for its analysis or in-progress attempt. */
function Row({ day, testID, onAnalysis, onResume }: { day: DayInfo; testID: string; onAnalysis: (id: string) => void; onResume: (id: string) => void }) {
  const live = dayAttempt(day)!; // the day's live attempt, or the archive practice of a day that was missed
  const s = live.summary;
  const resumable = !!live.resumable;
  const opens = `Result ${istTime(day.slot.closes_at)}`;
  const sealed = !resumable && !s && live.status === "embargoed";
  // Day is the short one; marks and status get the room, so "244/300" and "11:59 PM" are never cut.
  const facts: [string, string, number][] = [["Day", String(day.day), 0.6], ["Date", istDate(day.date), 1], ["Score", s ? `${s.score}/${s.maximum}` : "—", 1.2],
    sealed ? ["Result at", istTime(day.slot.closes_at), 1.2] : ["Status", resumable ? "Chal raha" : s ? "Scored" : "Taiyaari", 1.2]];
  return (
    <DCard testID={testID} style={{ gap: space.md }}>
      <View style={{ gap: 3 }}>
        <T w="heavy" size={10} color={colors.brandText} style={styles.caps}>DAY {day.day} · {istDate(day.date).toUpperCase()} · {live.mode === "series_live" ? "LIVE" : "PRACTICE"}</T>
        <T testID={`${testID}-title`} w="heavy" size={17} numberOfLines={2}>{live.title || day.slot.title}</T>
      </View>
      <View style={styles.facts}>
        {facts.map(([label, value, flex], i) => <View key={label} style={[styles.fact, { flex }, i > 0 && styles.factLine]}>
          <T w="heavy" size={15} numberOfLines={1}>{value}</T>
          <T size={10.5} color={colors.custom_eyebrow} numberOfLines={1}>{label}</T>
        </View>)}
      </View>
      {resumable
        ? <Pill testID={`${testID}-resume`} size="lg" icon="play" label="Attempt resume karo" onPress={() => onResume(live.id)} />
        : <AnalysisButton testID={`${testID}-analysis`} onPress={() => onAnalysis(live.id)}
            label={s ? "Analysis dekho" : live.status === "embargoed" ? opens : "Result dekho"} />}
    </DCard>
  );
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 1.6 },
  facts: { flexDirection: "row" },
  fact: { minWidth: 0, gap: 2, paddingHorizontal: space.sm },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
});

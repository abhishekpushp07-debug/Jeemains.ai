import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { useReducedMotion } from "react-native-reanimated";
import { Icon, Press, T } from "@/src/components/ui";
import { Pill, ProgressRing } from "@/src/components/design";
import { ExamCardFinish } from "@/src/components/ExamCardFinish";
import { WebsiteGradient } from "@/src/components/WebsiteGradient";
import { colors, examCardColors, pastel, SeriesTone, seriesHome, space } from "@/src/theme";
import { istDate } from "@/src/navigation";
import { DayInfo, Series, Streak, dayAction, skippedCount } from "@/src/series";

type CardState = { tone: SeriesTone; right: string; status: string; title: string; meta: string; action: { label: string; to: string; icon: any } };

function cardState(s: Series | null, days: DayInfo[]): CardState {
  const meta = "75 Q · 180 min · +4 / −1";
  if (!s) return { tone: "today", right: "62 DAYS", status: "All India JEE", title: "Checking today’s paper…", meta, action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  if (s.today < s.first_date) return { tone: "upcoming", right: "62 DAYS", status: `Starts ${istDate(s.first_date)}`, title: "62 daily full mocks", meta, action: { label: `Opens ${istDate(s.first_date)}`, to: "/live", icon: "calendar-clock" } };
  if (s.today > s.last_date) return { tone: "done", right: "62 / 62", status: "Series complete", title: "Practice archive is open", meta: "Every paper · practise anytime", action: { label: "Open archive", to: "/live", icon: "archive-outline" } };
  const d = days.find(x => x.isToday);
  if (!d) return { tone: "today", right: "62 DAYS", status: "Live series", title: s.title, meta, action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  const act = dayAction(d);
  const base = { right: `DAY ${d.day} / 62`, status: d.label, title: d.slot.title, meta };
  if (d.live && act) return { ...base, tone: d.tone, action: { label: d.live.resumable ? "Resume" : "View result", to: act.to, icon: act.icon } };
  if (d.live) return { ...base, tone: "done", action: { label: "Results at 11:59 PM", to: "/live", icon: "lock-clock" } };
  if (act) return { ...base, tone: "today", action: { label: "Start today’s test", to: act.to, icon: "arrow-right" } };
  if (d.slot.state === "start_closed") return { ...base, tone: "missed", action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  return { ...base, tone: "today", action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
}

// Original ruby-and-onyx All India banner surface; the status keeps its pastel as a small accent.
const palette = examCardColors("live");
const badge = seriesHome[".series-100ai-badge"];

export function HomeSeriesCard({ series, streak, days, error, shine, onToggleShine }: {
  series: Series | null; streak: Streak | null; days: DayInfo[]; error?: string; shine: boolean; onToggleShine: () => void;
}) {
  const router = useRouter();
  const reduced = useReducedMotion();
  const narrow = useWindowDimensions().width < 360;
  const st = cardState(series, days);
  const accent = pastel[st.tone].from;
  const done = streak?.completed_count ?? 0;
  const started = !!series && series.today >= series.first_date;
  return (
    <View testID="all-india-series-banner" style={styles.card}>
      <ExamCardFinish kind="live" enabled={shine} testID="series-home-finish" />
      <Press testID="series-open-hub-button" onPress={() => router.push("/live")} accessibilityLabel={`All India series. ${st.status}. ${st.title}. Open series hub`} scaleTo={0.985} style={{ gap: space.md }}>
        <View style={styles.top}>
          <T w="heavy" size={10} color={colors.custom_seriesBright} style={[styles.caps, { flexShrink: 1 }]} numberOfLines={1}>{narrow ? "ALL INDIA" : "ALL INDIA SERIES"}</T>
          <View testID="series-100ai-ribbon" style={styles.ai}>
            <WebsiteGradient value={badge.backgroundImage} />
            <T w="heavy" size={9.5} color={badge.color} accessibilityLabel="100% AI — series design branding">100% AI</T>
          </View>
          <View style={{ flex: 1 }} />
          <T testID="series-home-day" w="heavy" size={10} color={colors.custom_whiteA70} style={[styles.caps, narrow && { letterSpacing: 0.8 }]} numberOfLines={1}>{st.right}</T>
        </View>
        <View style={styles.body}>
          <ProgressRing testID="series-home-ring" size={narrow ? 76 : 88} stroke={9} value={done / 62} track={colors.custom_whiteA15} gradient={[colors.custom_seriesBright, colors.brandPrimary]} label={`${done} of 62 days done`}>
            <T w="heavy" size={18} color={palette.ink}>{Math.round((done / 62) * 100)}%</T>
            <T w="bold" size={9.5} color={colors.custom_whiteA70}>{done}/62 done</T>
          </ProgressRing>
          <View style={{ flex: 1, gap: 3 }}>
            <View style={styles.status}>
              <View style={[styles.dot, { backgroundColor: accent }]} />
              <T testID="series-availability-badge" w="heavy" size={10} color={accent} style={[styles.caps, { flexShrink: 1 }]} numberOfLines={1}>{st.status.toUpperCase()}</T>
            </View>
            <T testID="series-banner-title" w="heavy" size={17} color={palette.ink} numberOfLines={2}>{st.title}</T>
            <T testID="series-schedule-facts" size={12} color={palette.muted}>{st.meta}</T>
          </View>
        </View>
      </Press>
      <View style={styles.streak}>
          {started ? <>
            <Icon name="fire" size={16} color={colors.custom_flame} />
            <T testID="series-home-streak" w="bold" size={12} color={palette.ink}>{streak?.current_streak ?? 0}-day streak</T>
            <Icon name="cancel" size={14} color={colors.custom_whiteA70} style={{ marginLeft: space.sm }} />
            <T testID="series-home-skipped" w="bold" size={12} color={palette.ink}>{skippedCount(days)} skipped</T>
          </> : <T size={12} w="bold" color={palette.muted}>{series ? `${istDate(series.first_date)} – ${istDate(series.last_date)} · one mock a day` : error ? "Live status unavailable. Open the hub to retry." : "Loading schedule…"}</T>}
          <View style={{ flex: 1 }} />
          {!reduced ? <Press testID="home-series-shine-toggle" accessibilityRole="switch" accessibilityState={{ checked: shine }} accessibilityLabel="Card shine" onPress={onToggleShine} style={styles.toggle}>
            <Icon name={shine ? "pause" : "play"} size={14} color={colors.custom_whiteA70} />
          </Press> : null}
        </View>
      <Pill testID="home-series-cta" label={st.action.label} iconRight={st.action.icon} bg={palette.button} ink={palette.buttonInk} onPress={() => router.push(st.action.to as any)} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 26, padding: 20, gap: space.md, overflow: "hidden", backgroundColor: colors.custom_series, borderWidth: 1, borderColor: palette.line },
  top: { flexDirection: "row", alignItems: "center", gap: space.sm },
  caps: { letterSpacing: 1.8 },
  ai: { overflow: "hidden", borderRadius: 999, paddingHorizontal: 8, paddingVertical: 3 },
  body: { flexDirection: "row", alignItems: "center", gap: space.lg },
  status: { flexDirection: "row", alignItems: "center", gap: 6 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  streak: { flexDirection: "row", alignItems: "center", gap: 5, minHeight: 32 },
  toggle: { width: 44, height: 44, marginVertical: -6, marginRight: -10, alignItems: "center", justifyContent: "center", borderRadius: 22 },
});

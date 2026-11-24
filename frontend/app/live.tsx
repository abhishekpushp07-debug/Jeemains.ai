import React, { useRef, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { ErrorBox, Skeleton, T } from "@/src/components/ui";
import { DSheet, Pill, RoundButton, ScreenHeader, SectionLabel } from "@/src/components/design";
import { SeriesExplainer } from "@/src/components/SeriesBanner";
import { JourneyCard } from "@/src/components/series/JourneyCard";
import { DayCard, DayStrip, ResultsList, TodayCard } from "@/src/components/series/DayCards";
import { ScoreTrend, trendSummary } from "@/src/components/series/ScoreTrend";
import { DayMap } from "@/src/components/series/DayMap";
import { BoardLink } from "@/src/components/series/Board";
import { colors, space } from "@/src/theme";
import { ScreenMotion } from "@/src/motion";
import { DayInfo, dayAction, dayAttempt, istTime, seriesDays, todayPaper, useSeriesData, useSeriesWatch } from "@/src/series";

export default function Live() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { series, streak, history, days, reload } = useSeriesData(user?.id);
  useSeriesWatch(series.revalidate, days);
  const [open, setOpen] = useState(false);
  const [picked, setPicked] = useState<number | null>(null);
  const [confirm, setConfirm] = useState<DayInfo | null>(null);
  const scroll = useRef<React.ElementRef<typeof ScrollView>>(null);
  const stripY = useRef(0);
  const d = series.data;
  const total = seriesDays(d);
  const today = days.find(x => x.isToday);
  const selected = picked ?? today?.day ?? (d && d.today > d.last_date ? days.length : 1);
  const selectedDay = days.find(x => x.day === selected);
  const trend = trendSummary(days);
  const results = history.data?.items ?? [];
  const dayOf = (date?: string) => days.find(x => x.date === date)?.day;
  // The newest scored day before today: its marks sit on today's button until today's own result opens.
  const lastScored = [...days].reverse().find(x => !x.isToday && !!dayAttempt(x)?.summary);
  // A day chip / map cell: an attempted day opens its analysis (back lands on the AITS Analysis list, then here),
  // a running attempt resumes, a past day that was missed asks "Shuru karein?" and then starts. Today's own paper and an
  // upcoming day only show their card below (today's live paper starts from its full rules page). True = it did something.
  const openAnalysis = (id: string) => router.push({ pathname: "/result/[id]", params: { id, from: "series-day" } });
  const tapDay = (dd: DayInfo) => {
    setPicked(dd.day);
    const a = dayAttempt(dd);
    if (a) { if (a.resumable) router.push(`/attempt/${a.id}` as any); else openAnalysis(a.id); return true; }
    if (!dd.isToday && dayAction(dd)?.to.startsWith("/set/")) { setConfirm(dd); return true; }
    return false;
  };

  return (
    // The cards' shine rests while another screen (a paper, a result) is in front.
    <ScreenMotion>
    <View style={{ flex: 1, backgroundColor: colors.surface }}>
    <ScrollView ref={scroll} testID="series-hub" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom + space.xxl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={reload} />}>
      <View style={{ marginHorizontal: -space.lg, marginBottom: -space.md }}>
        <ScreenHeader testID="series-header" title="All India Series" eyebrow={`${total ? `${total} days` : "Daily mocks"} · Full syllabus`} backTestID="header-back-button"
          onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))}
          right={<RoundButton testID="series-tab-about" icon="information-variant" label="How it works" onPress={() => setOpen(true)} />} />
      </View>
      <View style={styles.brand}>
        <View testID="series-100ai-ribbon" style={styles.ai}><T w="bold" size={10} color={colors.brandText}>100% AI</T></View>
        <T size={12} color={colors.custom_eyebrow} style={{ flex: 1 }}>
          <T testID="series-score-200-tagline" w="heavy" size={12.5} color={colors.brandText}>Score 200+ with AI</T>
          <T testID="series-astra-credit" size={12} color={colors.custom_eyebrow}>{"  ·  "}Created by <T w="heavy" size={12} color={colors.custom_softText}>AI Astra</T></T>
        </T>
      </View>

      <ErrorBox error={series.error && !d ? series.error : ""} retry={series.reload} />
      {user ? <JourneyCard streak={streak.data} days={days} error={streak.error} retry={streak.reload} /> : null}

      {!d && !series.error ? <Skeleton h={190} style={{ borderRadius: 24 }} /> : null}
      {d ? <>
        <View style={{ gap: space.sm }}>
          <SectionLabel title="Today" right={<T testID="series-timing-note" size={11} color={colors.custom_eyebrow}>{today ? `Live ${istTime(today.slot.opens_at)} – ${istTime(today.slot.closes_at)} IST` : "Live 12:01 AM – 11:59 PM IST"}</T>} />
          {todayPaper(today) === "ready" ? <T testID="series-paper-ready" w="heavy" size={12} color={colors.custom_royalMid}>● Aaj ka paper ready hai — abhi shuru kar sakte ho</T> : null}
          <TodayCard series={d} day={today} last={lastScored} />
        </View>

        {user ? <BoardLink onPress={() => router.push("/series-leaderboard" as any)} /> : null}

        <View style={{ gap: space.sm }} onLayout={e => { stripY.current = e.nativeEvent.layout.y; }}>
          <SectionLabel title="All days" right={<T size={12} color={colors.muted}>swipe ›</T>} />
          <DayStrip days={days} selected={selected} onSelect={tapDay} />
          {selectedDay ? <DayCard day={selectedDay} /> : null}
        </View>

        <View style={{ gap: space.sm }}>
          <SectionLabel title="Score trend" right={trend ? <T testID="series-trend-summary" size={11.5} color={colors.muted}>Best {trend.best} · Avg {trend.avg}</T> : undefined} />
          <ScoreTrend days={days} />
        </View>

        {user ? <View style={{ gap: space.sm }}>
          <SectionLabel title="My results" action="AITS Analysis" onAction={() => router.push("/series-analysis")} actionTestID="series-open-analysis-list" />
          <ErrorBox error={history.error && !history.data ? history.error : ""} retry={history.reload} />
          {history.data ? <ResultsList items={results} dayOf={dayOf} limit={3} /> : !history.error ? <Skeleton h={60} style={{ borderRadius: 18 }} /> : null}
        </View> : null}

        <View style={{ gap: space.sm }}>
          <SectionLabel title={`${total}-day map`} />
          <DayMap days={days} selected={selected} onSelect={day => {
            const dd = days.find(x => x.day === day);
            if (dd && !tapDay(dd)) scroll.current?.scrollTo({ y: Math.max(0, stripY.current - space.sm), animated: true });
          }} />
        </View>
      </> : null}
    </ScrollView>
    <SeriesExplainer open={open} onClose={() => setOpen(false)} days={total} />
    <DSheet visible={!!confirm} onClose={() => setConfirm(null)} testID="series-start-confirm" title="Is din ka test shuru karein?">
      {confirm ? <>
        <T size={13.5} color={colors.custom_softText}>Day {confirm.day} · {confirm.slot.title}. 75 sawaal · 180 minute · +4 / −1. Haan dabate hi 60-second get-ready khulega, phir aapka timer chalega. Submit final hota hai.</T>
        {confirm.slot.state === "archive" ? <T testID="series-start-confirm-practice" size={12.5} color={colors.custom_eyebrow}>Yeh din nikal chuka hai, isliye yeh practice attempt hai — live streak aur live result mein nahi judega.</T> : null}
        {/* start=1: the paper's own page runs its usual checked start by itself, so there is no second Start button to press. */}
        <Pill testID="series-start-confirm-yes" size="lg" icon="play" label="Haan, shuru karo" onPress={() => { const sid = confirm.slot.set_id; setConfirm(null); if (sid) router.push({ pathname: "/set/[id]", params: { id: sid, start: "1" } }); }} />
        <Pill testID="series-start-confirm-no" kind="outline" label="Abhi nahi" onPress={() => setConfirm(null)} />
      </> : null}
    </DSheet>
    </View>
    </ScreenMotion>
  );
}

const styles = StyleSheet.create({
  brand: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: space.sm },
  ai: { backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
});

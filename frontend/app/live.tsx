import React, { useRef, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { ErrorBox, Skeleton, T } from "@/src/components/ui";
import { RoundButton, ScreenHeader, SectionLabel } from "@/src/components/design";
import { SeriesExplainer } from "@/src/components/SeriesBanner";
import { JourneyCard } from "@/src/components/series/JourneyCard";
import { DayCard, DayStrip, ResultsList, TodayCard } from "@/src/components/series/DayCards";
import { ScoreTrend, trendSummary } from "@/src/components/series/ScoreTrend";
import { DayMap } from "@/src/components/series/DayMap";
import { colors, space } from "@/src/theme";
import { useSeriesData } from "@/src/series";

export default function Live() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const { series, streak, history, days, reload } = useSeriesData(user?.id);
  const [open, setOpen] = useState(false);
  const [picked, setPicked] = useState<number | null>(null);
  const [allResults, setAllResults] = useState(false);
  const scroll = useRef<React.ElementRef<typeof ScrollView>>(null);
  const stripY = useRef(0);
  const d = series.data;
  const today = days.find(x => x.isToday);
  const selected = picked ?? today?.day ?? (d && d.today > d.last_date ? days.length : 1);
  const selectedDay = days.find(x => x.day === selected);
  const trend = trendSummary(days);
  const results = history.data?.items ?? [];
  const dayOf = (date?: string) => days.find(x => x.date === date)?.day;

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface }}>
    <ScrollView ref={scroll} testID="series-hub" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom + space.xxl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={reload} />}>
      <View style={{ marginHorizontal: -space.lg, marginBottom: -space.md }}>
        <ScreenHeader testID="series-header" title="All India Series" eyebrow="62 days · Full syllabus" backTestID="header-back-button"
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
          <SectionLabel title="Today" right={<T testID="series-timing-note" size={11} color={colors.custom_eyebrow}>Live 12:01 AM – 11:59 PM IST</T>} />
          <TodayCard series={d} day={today} />
        </View>

        <View style={{ gap: space.sm }} onLayout={e => { stripY.current = e.nativeEvent.layout.y; }}>
          <SectionLabel title="All days" right={<T size={12} color={colors.muted}>swipe ›</T>} />
          <DayStrip days={days} selected={selected} onSelect={setPicked} />
          {selectedDay ? <DayCard day={selectedDay} /> : null}
        </View>

        <View style={{ gap: space.sm }}>
          <SectionLabel title="Score trend" right={trend ? <T testID="series-trend-summary" size={11.5} color={colors.muted}>Best {trend.best} · Avg {trend.avg}</T> : undefined} />
          <ScoreTrend days={days} />
        </View>

        {user ? <View style={{ gap: space.sm }}>
          <SectionLabel title="My results" action={allResults ? "show less" : "view all"} onAction={results.length > 3 ? () => setAllResults(v => !v) : undefined} actionTestID="series-results-toggle" />
          <ErrorBox error={history.error && !history.data ? history.error : ""} retry={history.reload} />
          {history.data ? <ResultsList items={results} dayOf={dayOf} limit={allResults ? results.length : 3} /> : !history.error ? <Skeleton h={60} style={{ borderRadius: 18 }} /> : null}
        </View> : null}

        <View style={{ gap: space.sm }}>
          <SectionLabel title="62-day map" />
          <DayMap days={days} selected={selected} onSelect={day => { setPicked(day); scroll.current?.scrollTo({ y: Math.max(0, stripY.current - space.sm), animated: true }); }} />
        </View>
      </> : null}
    </ScrollView>
    <SeriesExplainer open={open} onClose={() => setOpen(false)} />
    </View>
  );
}

const styles = StyleSheet.create({
  brand: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: space.sm },
  ai: { backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
});

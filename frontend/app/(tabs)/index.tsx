import React, { useCallback } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api, rf } from "@/src/api/client";
import { cancelPrefetch, prefetch, useCached } from "@/src/useCached";
import { Notice, Press, T } from "@/src/components/ui";
import { SectionLabel } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { HomeSeriesCard } from "@/src/components/series/HomeSeriesCard";
import { ChipItem, ContinueCard, ExamGrid, ExploreChips, ForYou, GridItem } from "@/src/components/home/HomeParts";
import { ShareCard } from "@/src/components/home/ShareCard";
import { useShare } from "@/src/components/SeriesBanner";
import { BrandMark } from "@/src/components/BrandMark";
import { getPyqCatalogue } from "@/src/api/pyq";
import { colors, space } from "@/src/theme";
import { EXAMS, istDate, usesNativeTabs } from "@/src/navigation";
import { seriesDays, todayPaper, useSeriesData, useSeriesWatch } from "@/src/series";
import { examIcon, useExams } from "@/src/api/examCatalog";
import { useListFocus } from "@/src/useListFocus";
import { HomeDream } from "@/src/dream/HomeDream";
import { ScreenMotion } from "@/src/motion";

const greeting = () => { const h = new Date().getHours(); return h < 5 ? "good night" : h < 12 ? "good morning" : h < 17 ? "good afternoon" : "good evening"; };
// The three exams keep their own tile look; the names come from the website.
const TILE: Record<string, Omit<GridItem, "id" | "label" | "to">> = {
  "jee-main": { icon: "atom-variant", value: "pyq papers", badge: "PYQ" },
  bitsat: { icon: "school-outline", value: "mock tests" },
  comedk: { icon: "office-building-outline", value: "mock tests" },
};
// Shown while the website's list is on its way, so the grid never jumps.
const BUILT_IN_TILES = EXAMS.map(e => ({ slug: e.slug, name: e.name }));

export default function Home() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const share = useShare();
  const { user, expired } = useAuth();
  const uid = user?.id;
  const { series, streak, days, reload } = useSeriesData(uid, false);
  useSeriesWatch(series.revalidate, days);
  const progress = useCached<any>(user ? `u.${user.id}.progress` : null, (signal) => api("/my/tests?tab=progress&page=1", { signal }));
  const catalog = useExams();
  useListFocus(catalog.revalidate);
  const current = progress.data?.items?.[0];
  const counts = progress.data?.counts;
  useFocusEffect(useCallback(() => {
    if (!uid) return;
    // One ordered background lane; don't flood canonical with speculative
    // requests while the first screen is still loading. Navigation promotes demand.
    const t = setTimeout(() => {
      prefetch(`u.${uid}.pyq.jee-main`, signal => getPyqCatalogue(signal), false);
      prefetch("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
    }, 300);
    return () => { clearTimeout(t); cancelPrefetch(`u.${uid}.`); };
  }, [uid]));
  const bottom = usesNativeTabs ? insets.bottom : 0;
  const s = series.data;
  const today = days.find(d => d.isToday);
  const total = seriesDays(s); // the website's schedule decides the day count
  const liveSub = !s ? "daily full mocks" : s.today < s.first_date ? `opens ${istDate(s.first_date).toLowerCase()}` : s.today > s.last_date ? "practice archive" : todayPaper(today) === "ready" ? `day ${today!.day} · paper ready` : today ? `day ${today.day} · ${today.label.toLowerCase()}` : `${total}-day series`;
  const first = user?.name?.trim().split(/\s+/)[0];
  const openTests = (tab: string) => router.push({ pathname: "/(tabs)/tests", params: { tab, at: String(Date.now()) } });
  // Shortcuts to an exam disappear with it when the owner hides that exam on the website.
  const shown = (slug: string) => !catalog.exams || catalog.exams.some(e => e.slug === slug);
  const badge = (key: string, word: string) => counts?.[key] ? `${counts[key]} ${word}` : undefined;

  const exams: GridItem[] = [
    // The website's own exam list, in its order: a new exam gets its own tile, a hidden one disappears.
    ...(catalog.exams ?? BUILT_IN_TILES).map((e, i) => TILE[e.slug] ? { ...TILE[e.slug], id: e.slug, label: e.name.toUpperCase(), to: `/exam/${e.slug}` }
      : { id: e.slug, icon: examIcon(e.slug, i), label: e.name.toUpperCase(), value: "practice tests", to: `/exam/${e.slug}` }),
    { id: "live", icon: "calendar-check-outline", label: "ALL INDIA", value: liveSub, badge: "LIVE", to: "/live" },
  ];

  return (
    <ScrollView
      testID="home-screen"
      style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: bottom + space.xxl, paddingHorizontal: space.lg, gap: space.xxl }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { reload(); progress.reload(); catalog.reload(); }} />}
    >
      <View style={{ gap: space.lg }}>
        <View testID="home-header" style={styles.header}>
          <BrandMark testID="home-brand" height={44} />
          <Press testID="home-account-button" onPress={() => router.push("/account")} accessibilityLabel="Account" style={styles.account}>
            <Glyph name="account-outline" size={22} color={colors.onSurface} stroke={1.5} />
          </Press>
        </View>
        <View style={{ gap: 2 }}>
          <T testID="home-greeting" w="heavy" size={26}>{greeting()}{first ? `, ${first.toLowerCase()}` : ""}.</T>
          <T size={14} color={colors.muted}>one focused step today.</T>
        </View>
      </View>

      {expired ? (
        <Notice tone="warning" testID="home-session-expired">
          <T size={13} w="medium" color={colors.warning}>Your session ended. Pending drafts on this phone are safe. Re-enter your number from Account to continue the same profile.</T>
        </Notice>
      ) : null}

      <View style={{ gap: space.md }}>
        <SectionLabel title="All India series" onAction={() => router.push("/live")} actionTestID="home-series-view-all" />
        {/* The card's shine rests while another tab or screen is in front. */}
        <ScreenMotion><HomeSeriesCard series={s} streak={streak.data} days={days} error={series.error} /></ScreenMotion>
      </View>

      {current ? <View style={{ gap: space.md }}>
        <SectionLabel title="Continue" />
        <ContinueCard attempt={current} onPress={() => router.push(`/attempt/${current.id}`)} />
      </View> : null}

      <View style={{ gap: space.md }}>
        <SectionLabel title="Practice" testID="home-exams-label" />
        <ExamGrid items={exams} />
      </View>

      <View style={{ gap: space.lg }}>
        <SectionLabel title="For you" onAction={() => router.push("/(tabs)/tests")} actionTestID="home-my-tests-entry" />
        <ForYou items={[
          { id: "progress", icon: "clock-outline", label: "in\nprogress", badge: badge("progress", "ACTIVE"), onPress: () => openTests("progress"), testID: "home-tests-stat-progress", badgeTestID: "home-tests-count-progress" },
          { id: "saved", icon: "bookmark-outline", label: "saved\npapers", badge: badge("saved", "SAVED"), onPress: () => openTests("saved"), testID: "home-tests-stat-saved", badgeTestID: "home-tests-count-saved" },
          { id: "completed", icon: "chart-box-outline", label: "my\nresults", badge: badge("completed", "DONE"), onPress: () => openTests("completed"), testID: "home-tests-stat-completed", badgeTestID: "home-tests-count-completed" },
          { id: "rapid", icon: "lightning-bolt", label: "rapid\nfire", badge: "DUEL", onPress: () => router.push("/(tabs)/rapid"), testID: "home-rapid-fire-entry" },
        ]} />
      </View>

      <HomeDream />

      <View style={{ gap: space.md }}>
        <SectionLabel title="Explore JEELIVE" />
        <ExploreChips items={([
          { id: "pyq", exam: "jee-main", icon: "file-document-check-outline", label: "pyq papers", tint: colors.brandText, onPress: () => router.push("/pyq") },
          { id: "chapters", exam: "jee-main", icon: "book-open-page-variant-outline", label: "chapter-wise", tint: colors.custom_qMarkedInk, onPress: () => router.push("/catalogue?slug=jee-main&kind=chapters") },
          { id: "series", icon: "calendar-check-outline", label: "all india series", tint: colors.onSurface, onPress: () => router.push("/live") },
          { id: "bitsat", exam: "bitsat", icon: "school-outline", label: "bitsat mocks", tint: colors.custom_timerAmber, onPress: () => router.push("/catalogue?slug=bitsat&kind=mocks") },
          { id: "comedk", exam: "comedk", icon: "office-building-outline", label: "comedk mocks", tint: colors.custom_softText, onPress: () => router.push("/catalogue?slug=comedk&kind=mocks") },
          { id: "history", exam: "jee-main", icon: "history", label: "results & history", tint: colors.custom_savedBlue, onPress: () => router.push("/catalogue?slug=jee-main&kind=history") },
          { id: "share", icon: "share-variant", label: "share with friends", tint: colors.success, onPress: share },
          { id: "mission", icon: "compass-outline", label: "our mission", tint: colors.brandText, onPress: () => router.push("/(tabs)/mission") },
        ] as (ChipItem & { exam?: string })[]).filter(c => !c.exam || shown(c.exam))} />
      </View>

      <ShareCard />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  account: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
});

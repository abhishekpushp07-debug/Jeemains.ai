import React, { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { api, rf } from "@/src/api/client";
import { cancelPrefetch, prefetch, useCached } from "@/src/useCached";
import { Icon, Notice, Press, T } from "@/src/components/ui";
import { DCard, SectionLabel } from "@/src/components/design";
import { ExamTile, TileKind } from "@/src/components/ExamTile";
import { HomeSeriesCard } from "@/src/components/series/HomeSeriesCard";
import { BrandMark } from "@/src/components/BrandMark";
import { getPyqCatalogue } from "@/src/api/pyq";
import { colors, radius, space } from "@/src/theme";
import { fmtClock, usesNativeTabs } from "@/src/navigation";
import { useSeriesData } from "@/src/series";

type Tile = { id: string; kind: TileKind; title: string; sub: string; to: string; badge?: string };
const TILES: Tile[] = [
  { id: "jee-main", kind: "jee", badge: "PYQ", title: "JEE Main", sub: "PYQs · Chapters", to: "/exam/jee-main" },
  { id: "live", kind: "live", badge: "100% AI", title: "Live JEE Series", sub: "All India series", to: "/live" },
  { id: "bitsat", kind: "bitsat", title: "BITSAT", sub: "Practice · Branches", to: "/exam/bitsat" },
  { id: "comedk", kind: "comedk", title: "COMEDK", sub: "Practice · History", to: "/exam/comedk" },
];
const STATS = [["progress", "In progress", colors.custom_timerAmber], ["saved", "Saved", colors.custom_savedBlue], ["completed", "Completed", colors.custom_mint]] as const;

export default function Home() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, expired } = useAuth();
  const uid = user?.id;
  const [shine, setShine] = useState(true);
  const reducedMotion = useReducedMotion();
  const { series, streak, days, reload } = useSeriesData(uid, false);
  const progress = useCached<any>(user ? `u.${user.id}.progress` : null, (signal) => api("/my/tests?tab=progress&page=1", { signal }));
  const current = progress.data?.items?.[0];
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
  const liveSub = !s ? "All India series" : s.today < s.first_date ? "Opens 1 Dec" : s.today > s.last_date ? "Practice archive" : today ? `Day ${today.day} · ${today.label}` : "All India series";
  const enter = (i: number) => reducedMotion ? undefined : FadeInDown.delay(50 * i).duration(320);

  return (
    <ScrollView
      testID="home-screen"
      style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: bottom + space.xxl, paddingHorizontal: space.lg, gap: space.xl }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { reload(); progress.reload(); }} />}
    >
      <View testID="home-header" style={styles.header}>
        <BrandMark testID="home-brand" />
        <Press testID="home-account-button" onPress={() => router.push("/account")} accessibilityLabel="Account" style={styles.account}>
          <Icon name="account-circle-outline" size={20} color={colors.onSurface} />
          <T w="bold" size={13}>{user?.phone ? "··" + user.phone.slice(-4) : "Account"}</T>
        </Press>
      </View>

      {expired ? (
        <Notice tone="warning" testID="home-session-expired">
          <T size={13} w="medium" color={colors.warning}>Your session ended. Pending drafts on this phone are safe. Re-enter your number from Account to continue the same profile.</T>
        </Notice>
      ) : null}

      <Animated.View entering={enter(0)}>
        <HomeSeriesCard series={s} streak={streak.data} days={days} error={series.error} shine={shine} onToggleShine={() => setShine(v => !v)} />
      </Animated.View>

      {current ? (
        <Animated.View entering={enter(1)}>
          <Press testID="home-continue-attempt" onPress={() => router.push(`/attempt/${current.id}`)} accessibilityLabel={`Resume ${current.title}`} scaleTo={0.985}>
            <DCard style={styles.continue}>
              <View style={styles.play}><Icon name="play" size={20} color={colors.custom_mint} /></View>
              <View style={{ flex: 1, gap: 2 }}>
                <T w="bold" size={14} numberOfLines={1}>{current.title}</T>
                <T size={11.5} color={colors.muted} numberOfLines={1}>{current.saved_answers}/{current.count} saved{current.remaining_seconds ? " · " + fmtClock(Math.round(current.remaining_seconds)) + " left" : ""}</T>
              </View>
              <View testID="home-continue-resume" style={styles.resume}><T w="heavy" size={13} color={colors.custom_bar}>Resume</T></View>
            </DCard>
          </Press>
        </Animated.View>
      ) : null}

      <View style={{ gap: space.lg }}>
        <SectionLabel title="Exams" testID="home-exams-label" />
        <View testID="home-exam-grid" style={styles.grid}>
          {TILES.map((t, i) => (
            <Animated.View key={t.id} entering={enter(2 + i)} style={styles.cell}>
              <ExamTile testID={"home-tile-" + t.id} kind={t.kind} title={t.title} sub={t.id === "live" ? liveSub : t.sub} badge={t.badge}
                onPress={() => router.push(t.to as any)} />
            </Animated.View>
          ))}
        </View>
      </View>

      <View style={{ gap: space.sm }}>
        <SectionLabel title="My tests" onAction={() => router.push("/(tabs)/tests")} actionTestID="home-my-tests-entry" />
        <View style={styles.stats}>
          {STATS.map(([key, label, tint]) => (
            <Press key={key} testID={"home-tests-stat-" + key} onPress={() => router.push({ pathname: "/(tabs)/tests", params: { tab: key, at: String(Date.now()) } })} accessibilityLabel={`${label}: ${progress.data?.counts?.[key] ?? "loading"}`} style={styles.stat}>
              <T testID={`home-tests-count-${key}`} w="heavy" size={22} color={tint}>{progress.data?.counts ? String(progress.data.counts[key]) : "–"}</T>
              <T size={11} color={colors.muted} numberOfLines={1}>{label}</T>
            </Press>
          ))}
        </View>
      </View>

      <Press testID="home-rapid-fire-entry" onPress={() => router.push("/(tabs)/rapid")} accessibilityLabel="Rapid Fire. Solo or duel" scaleTo={0.985}>
        <DCard style={styles.rapid}>
          <View style={styles.bolt}><Icon name="lightning-bolt" size={22} color={colors.custom_gold} /></View>
          <View style={{ flex: 1, gap: 2 }}>
            <T w="bold" size={14}>Rapid Fire · Solo or Duel</T>
            <T size={11.5} color={colors.muted}>30 cards · 20 s each · challenge a friend</T>
          </View>
          <Icon name="chevron-right" size={22} color={colors.custom_eyebrow} />
        </DCard>
      </Press>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  account: { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: space.lg, height: 44, borderRadius: radius.pill, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  continue: { flexDirection: "row", alignItems: "center", gap: space.md, paddingVertical: space.md, paddingHorizontal: space.lg },
  play: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.xl, paddingTop: space.sm },
  cell: { width: "48%" },
  stats: { flexDirection: "row", gap: space.md },
  stat: { flex: 1, minWidth: 0, minHeight: 72, borderRadius: 18, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, paddingHorizontal: space.md, paddingVertical: space.md, justifyContent: "center", gap: 2 },
  resume: { height: 40, paddingHorizontal: 16, borderRadius: radius.pill, backgroundColor: colors.onSurface, alignItems: "center", justifyContent: "center" },
  rapid: { flexDirection: "row", alignItems: "center", gap: space.md, paddingVertical: space.md, borderRadius: 18 },
  bolt: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.custom_goldSoft, borderWidth: 1, borderColor: colors.custom_goldDeep, alignItems: "center", justifyContent: "center" },
});

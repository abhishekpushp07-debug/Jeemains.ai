import React, { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { api, rf } from "@/src/api/client";
import { cancelPrefetch, prefetch, useCached } from "@/src/useCached";
import { Card, Icon, Notice, Press, T } from "@/src/components/ui";
import { SeriesBanner, Series } from "@/src/components/SeriesBanner";
import { ExamTile, TileKind } from "@/src/components/ExamTile";
import { BrandMark } from "@/src/components/BrandMark";
import { getPyqCatalogue } from "@/src/api/pyq";
import { colors, radius, space } from "@/src/theme";
import { fmtClock, usesNativeTabs } from "@/src/navigation";

type Tile = { id: string; kind: TileKind; title: string; sub: string; to: string; badge?: string };
const TILES: Tile[] = [
  { id: "jee-main", kind: "jee", badge: "PYQ", title: "JEE Main", sub: "PYQs · Chapters", to: "/exam/jee-main" },
  { id: "live", kind: "live", badge: "100% AI", title: "Live JEE Series", sub: "All India series", to: "/live" },
  { id: "bitsat", kind: "bitsat", title: "BITSAT", sub: "Practice · Branches", to: "/exam/bitsat" },
  { id: "comedk", kind: "comedk", title: "COMEDK", sub: "Practice · History", to: "/exam/comedk" },
];

export default function Home() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, expired } = useAuth();
  const [shine, setShine] = useState(true);
  const reducedMotion = useReducedMotion();
  const series = useCached<Series>("series", (signal) => api("/series/all-india-jee", { signal }));
  const progress = useCached<any>(user ? `u.${user.id}.progress` : null, (signal) => api("/my/tests?tab=progress&page=1", { signal }));
  const current = progress.data?.items?.[0];
  useFocusEffect(useCallback(() => {
    if (!user) return;
    // One ordered background lane; don't flood canonical with five speculative
    // requests while the first screen is still loading. Navigation promotes demand.
    const t = setTimeout(() => {
      prefetch("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", user.id));
      prefetch(`u.${user.id}.pyq.jee-main`, signal => getPyqCatalogue(signal));
    }, 700);
    return () => { clearTimeout(t); cancelPrefetch(`u.${user.id}.`); };
  }, [user]));
  const bottom = usesNativeTabs ? insets.bottom : 0;

  return (
    <ScrollView
      testID="home-screen"
      style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: bottom + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { series.reload(); progress.reload(); }} />}
    >
      <View testID="home-header" style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <BrandMark testID="home-brand" />
        <Press testID="home-account-button" onPress={() => router.push("/account")} accessibilityLabel="Account" style={{ flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: space.md, height: 44, borderRadius: radius.pill, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}>
          <Icon name="account-circle-outline" size={20} color={colors.onSurface} />
          <T w="bold" size={12}>{user?.phone ? "··" + user.phone.slice(-4) : "Account"}</T>
        </Press>
      </View>

      {expired ? (
        <Notice tone="warning" testID="home-session-expired">
          <T size={13} w="medium" color={colors.warning}>Your session ended. Pending drafts on this phone are safe. Re-enter your number from Account to continue the same profile.</T>
        </Notice>
      ) : null}

      {current ? (
        <Animated.View entering={reducedMotion ? undefined : FadeInDown.duration(350)}>
          <Press testID="home-continue-attempt" onPress={() => router.push(`/attempt/${current.id}`)} style={{ borderRadius: radius.lg, overflow: "hidden" }}>
            <LinearGradient colors={[colors.custom_darkCard, colors.surfaceInverse]} style={{ padding: space.lg, flexDirection: "row", alignItems: "center", gap: space.md }}>
              <View style={{ width: 48, height: 48, borderRadius: 24, backgroundColor: colors.success, alignItems: "center", justifyContent: "center" }}>
                <Icon name="play" size={26} color={colors.onSuccess} />
              </View>
              <View style={{ flex: 1 }}>
                <T w="bold" size={11} color={colors.custom_whiteA70} style={{ letterSpacing: 1 }}>CONTINUE YOUR ATTEMPT</T>
                <T w="heavy" size={16} color={colors.onSurfaceInverse} numberOfLines={1}>{current.title}</T>
                <T size={12} color={colors.custom_whiteA70}>{current.exam} · {current.saved_answers}/{current.count} saved{current.remaining_seconds ? " · " + fmtClock(Math.round(current.remaining_seconds)) + " left" : ""}</T>
              </View>
              <Icon name="chevron-right" size={24} color={colors.onSurfaceInverse} />
            </LinearGradient>
          </Press>
        </Animated.View>
      ) : null}

      <View testID="home-exam-grid" style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.lg }}>
        {TILES.map((t, i) => (
          <Animated.View key={t.id} entering={reducedMotion ? undefined : FadeInDown.delay(60 * i).duration(380)} style={{ width: "48%" }}>
            <ExamTile testID={"home-tile-" + t.id} kind={t.kind} title={t.title} sub={t.sub} shine={shine} badge={t.badge} onPress={() => router.push(t.to as any)} />
          </Animated.View>
        ))}
      </View>

      <Press testID="home-rapid-fire-entry" onPress={() => router.push("/(tabs)/rapid")} style={{ borderRadius: radius.lg, overflow: "hidden" }}>
        <LinearGradient colors={[colors.custom_warningSoft, colors.brandTertiary]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ padding: space.lg, flexDirection: "row", alignItems: "center", gap: space.md, borderWidth: 1, borderColor: colors.border, borderRadius: radius.lg }}>
          <View style={{ width: 48, height: 48, borderRadius: 14, backgroundColor: colors.custom_amber, alignItems: "center", justifyContent: "center" }}>
            <Icon name="lightning-bolt" size={28} color={colors.onBrandPrimary} />
          </View>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={16}>Rapid Fire · Solo or Duel</T>
            <T size={12} color={colors.muted}>30 formula cards · 20 s each · challenge a friend</T>
          </View>
          <Icon name="chevron-right" size={24} color={colors.onSurface} />
        </LinearGradient>
      </Press>

      <View style={styles.finishControls}>
        <T testID="home-series-section-label" size={11} w="bold" color={colors.muted} style={styles.eyebrow}>ALL INDIA SERIES</T>
        {!reducedMotion ? <Press testID="home-series-shine-toggle" accessibilityRole="switch" accessibilityState={{ checked: shine }} accessibilityLabel="Animated live-series banner finish" onPress={() => setShine((value) => !value)} style={styles.shineToggle}>
          <Icon name={shine ? "pause-circle-outline" : "play-circle-outline"} size={16} color={colors.muted} />
          <T testID="home-series-shine-label" size={11} color={colors.muted}>{shine ? "Pause shine" : "Play shine"}</T>
        </Press> : null}
      </View>
      <SeriesBanner series={series.data} error={series.error} home shine={shine} />

      <Press testID="home-my-tests-entry" onPress={() => router.push("/(tabs)/tests")}>
        <Card style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
          <Icon name="clipboard-text-clock-outline" size={26} color={colors.brandText} />
          <View style={{ flex: 1 }}>
            <T w="bold" size={15}>My Tests</T>
            <T size={12} color={colors.muted}>{progress.data ? `${progress.data.counts.progress} in progress · ${progress.data.counts.saved} saved · ${progress.data.counts.completed} completed` : "In progress · Saved · Completed"}</T>
          </View>
          <Icon name="chevron-right" size={22} color={colors.muted} />
        </Card>
      </Press>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  eyebrow: { letterSpacing: 1.2, marginBottom: space.sm },
  finishControls: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: space.sm },
  shineToggle: { minHeight: 44, paddingHorizontal: space.md, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.border, flexDirection: "row", alignItems: "center", gap: 5, backgroundColor: colors.surfaceSecondary },
});

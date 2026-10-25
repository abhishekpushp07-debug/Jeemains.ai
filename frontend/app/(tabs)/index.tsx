import React, { useEffect } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { api, rf } from "@/src/api/client";
import { prefetch, useCached } from "@/src/useCached";
import { Card, Icon, Notice, Press, T } from "@/src/components/ui";
import { SeriesBanner, Series } from "@/src/components/SeriesBanner";
import { ExamTile, TileKind } from "@/src/components/ExamTile";
import { colors, radius, space } from "@/src/theme";
import { fmtClock, usesNativeTabs } from "@/src/navigation";

type Tile = { id: string; kind: TileKind; title: string; sub: string; grad: [string, string]; to: string; badge?: string };
const TILES: Tile[] = [
  { id: "jee-main", kind: "jee", badge: "HOT", title: "JEE Main", sub: "Mocks · Chapters", grad: [colors.custom_examJee, colors.custom_examJeeDeep], to: "/exam/jee-main" },
  { id: "live", kind: "live", badge: "100% AI", title: "Live JEE Series", sub: "62-day All India", grad: [colors.custom_seriesBright, colors.custom_series], to: "/live" },
  { id: "bitsat", kind: "bitsat", title: "BITSAT", sub: "Practice · Branches", grad: [colors.custom_examBitsat, colors.custom_examBitsatDeep], to: "/exam/bitsat" },
  { id: "comedk", kind: "comedk", title: "COMEDK", sub: "Practice · History", grad: [colors.custom_darkCard, colors.custom_examComedk], to: "/exam/comedk" },
];

export default function Home() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, expired } = useAuth();
  const series = useCached<Series>("series", (signal) => api("/series/all-india-jee", { signal }));
  const progress = useCached<any>(user ? `u.${user.id}.progress` : null, (signal) => api("/my/tests?tab=progress&page=1", { signal }));
  const current = progress.data?.items?.[0];
  useEffect(() => {
    if (!user) return;
    // Warm the next likely screens so they open instantly.
    const t = setTimeout(() => {
      for (const slug of ["jee-main", "bitsat"]) {
        const path = `/exam-navigation/${slug}/catalogue?${new URLSearchParams({ kind: "chapters", subject: "Physics", q: "", page: "1" })}`;
        prefetch(`u.${user.id}.${path}`, () => api(path));
      }
      prefetch("rf.catalog", () => rf("/catalog", user.id));
      prefetch(`u.${user.id}.streak`, () => api("/series/all-india-jee/streak"));
    }, 400);
    return () => clearTimeout(t);
  }, [user]);
  const bottom = usesNativeTabs ? insets.bottom : 0;

  return (
    <ScrollView
      testID="home-screen"
      style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: bottom + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { series.reload(); progress.reload(); }} />}
    >
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <View style={{ borderRadius: 12, padding: 4, backgroundColor: "#FFFFFF", borderWidth: 1.5, borderColor: colors.custom_neonAmber }}><Image source={require("../../assets/images/jeelive-logo.webp")} style={{ width: 132, height: 40 }} contentFit="contain" accessibilityLabel="JEELIVE.AI" /></View>
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
        <Animated.View entering={FadeInDown.duration(350)}>
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

      <View>
        <T w="heavy" size={20}>Choose your exam</T>
        <T size={13} color={colors.muted}>Start new practice or pick up where you stopped.</T>
      </View>

      <View style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.lg }}>
        {TILES.map((t, i) => (
          <Animated.View key={t.id} entering={FadeInDown.delay(60 * i).duration(380)} style={{ width: "48%" }}>
            <ExamTile testID={"home-tile-" + t.id} kind={t.kind} title={t.title} sub={t.sub} grad={t.grad} badge={t.badge} onPress={() => router.push(t.to as any)} />
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

      <SeriesBanner series={series.data} error={series.error} />

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

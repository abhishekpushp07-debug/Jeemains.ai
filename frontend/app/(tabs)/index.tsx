import React from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { api } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Card, Icon, IconName, Notice, Press, T } from "@/src/components/ui";
import { SeriesBanner, Series } from "@/src/components/SeriesBanner";
import { colors, radius, space } from "@/src/theme";
import { fmtClock, usesNativeTabs } from "@/src/navigation";

type Tile = { id: string; title: string; sub: string; icon: IconName; grad: [string, string]; to: string; art: number };
const TILES: Tile[] = [
  { id: "jee-main", title: "JEE Main", sub: "Mocks · Chapters", icon: "atom-variant", grad: [colors.custom_examJee, colors.custom_examJeeDeep], to: "/exam/jee-main", art: require("../../assets/images/tile-jee.jpg") },
  { id: "live", title: "Live JEE Series", sub: "62-day All India", icon: "diamond-stone", grad: [colors.custom_seriesBright, colors.custom_series], to: "/(tabs)/live", art: require("../../assets/images/tile-live.jpg") },
  { id: "bitsat", title: "BITSAT", sub: "Practice · Branches", icon: "rocket-launch", grad: [colors.custom_examBitsat, colors.custom_examBitsatDeep], to: "/exam/bitsat", art: require("../../assets/images/tile-bitsat.jpg") },
  { id: "comedk", title: "COMEDK", sub: "Practice · History", icon: "crown", grad: [colors.custom_darkCard, colors.custom_examComedk], to: "/exam/comedk", art: require("../../assets/images/tile-comedk.jpg") },
];

export default function Home() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user, expired } = useAuth();
  const series = useCached<Series>("series", (signal) => api("/series/all-india-jee", { signal }));
  const progress = useCached<any>(user ? `u.${user.id}.progress` : null, (signal) => api("/my/tests?tab=progress&page=1", { signal }));
  const current = progress.data?.items?.[0];
  const bottom = usesNativeTabs ? insets.bottom : 0;

  return (
    <ScrollView
      testID="home-screen"
      style={{ flex: 1, backgroundColor: colors.surface }}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: bottom + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { series.reload(); progress.reload(); }} />}
    >
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <Image source={require("../../assets/images/jeelive-logo.webp")} style={{ width: 150, height: 48 }} contentFit="contain" accessibilityLabel="JEELIVE.AI" />
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

      <View style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", rowGap: space.md }}>
        {TILES.map((t, i) => (
          <Animated.View key={t.id} entering={FadeInDown.delay(60 * i).duration(380)} style={{ width: "48%" }}>
            <Press testID={"home-tile-" + t.id} onPress={() => router.push(t.to as any)} accessibilityLabel={t.title}>
              <Card style={{ padding: 0, overflow: "hidden" }}>
                <Image source={t.art} style={{ width: "100%", height: 112, backgroundColor: t.grad[0] }} contentFit="cover" contentPosition="center" accessibilityLabel={t.title + " artwork"} transition={0} />
                {t.id === "jee-main" || t.id === "live" ? (
                  <View style={{ position: "absolute", top: 8, ...(t.id === "live" ? { left: 8 } : { right: 8 }), flexDirection: "row", alignItems: "center", gap: 2, backgroundColor: t.id === "live" ? colors.custom_seriesBright : colors.custom_burgundy, borderRadius: radius.sm, paddingHorizontal: 6, paddingVertical: 2, borderWidth: 1, borderColor: colors.custom_whiteA15 }}>
                    <T w="heavy" size={10} color={colors.onBrandPrimary}>{t.id === "live" ? "100% AI" : "HOT"}</T>
                    <Icon name="star-four-points" size={9} color={colors.onBrandPrimary} />
                  </View>
                ) : null}
                <View style={{ padding: space.md, gap: 2 }}>
                  <T w="heavy" size={16} numberOfLines={1}>{t.title}</T>
                  <T size={12} color={colors.muted} numberOfLines={1}>{t.sub}</T>
                </View>
              </Card>
            </Press>
          </Animated.View>
        ))}
      </View>

      <Press testID="home-rapid-fire-entry" onPress={() => router.push("/(tabs)/rapid")} style={{ borderRadius: radius.lg, overflow: "hidden" }}>
        <LinearGradient colors={[colors.custom_warningSoft, colors.brandTertiary]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ padding: space.lg, flexDirection: "row", alignItems: "center", gap: space.md, borderWidth: 1, borderColor: colors.border, borderRadius: radius.lg }}>
          <View style={{ width: 48, height: 48, borderRadius: 14, backgroundColor: colors.custom_amber, alignItems: "center", justifyContent: "center" }}>
            <Icon name="lightning-bolt" size={28} color={colors.onBrandPrimary} />
          </View>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={16}>Rapid Fire · 3-minute burst</T>
            <T size={12} color={colors.muted}>10 formula & concept cards · 20 seconds each</T>
          </View>
          <Icon name="chevron-right" size={24} color={colors.onSurface} />
        </LinearGradient>
      </Press>

      <SeriesBanner series={series.data} error={series.error} />

      <Press testID="home-my-tests-entry" onPress={() => router.push("/(tabs)/tests")}>
        <Card style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
          <Icon name="clipboard-text-clock-outline" size={26} color={colors.brandPrimary} />
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

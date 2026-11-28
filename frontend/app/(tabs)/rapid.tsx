import React, { useCallback, useEffect, useRef, useState } from "react";
import { BackHandler, StyleSheet, View } from "react-native";
import { useFocusEffect, usePathname, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { rf } from "@/src/api/client";
import { prefetch } from "@/src/useCached";
import { withRapid } from "@/src/rapid/ui";
import { ArenaBg } from "@/src/rapid/arena";
import { ArenaBar } from "@/src/rapid/ArenaBar";
import { TopStrip } from "@/src/rapid/TopStrip";
import { ChallengeBanner } from "@/src/rapid/ChallengeBanner";
import { LobbyTab } from "@/src/rapid/LobbyTab";
import { TrophyTab } from "@/src/rapid/TrophyTab";
import { GangTab } from "@/src/rapid/GangTab";
import { StoreTab } from "@/src/rapid/StoreTab";
import { go, setArenaTab, useArenaTab } from "@/src/rapid/social";
import { useAuth } from "@/src/auth";
import { DailyPopup } from "@/src/rapid/DailyPopup";
import { useDaily, useDailyLook } from "@/src/rapid/daily";
import { enterFeature } from "@/src/featureTrack";

// The Crimson Arena: Rapid Fire's own world with its own bottom bar. The app's bar hides while this tab is open.
/**
 * Every time a student comes into Rapid Fire (from Home or any other part of the app, not back from a match), today's
 * All India round is offered first until it is played. ENTER opens the cards; EXIT stays on the Rapid Fire home.
 */
function useDailyOffer() {
  const path = usePathname(), last = useRef<string | null>(null);
  const [ask, setAsk] = useState(false);
  useEffect(() => {
    const prev = last.current;
    last.current = path;
    if (path === "/rapid" && (prev === null || !prev.startsWith("/rapid"))) setAsk(true);
  }, [path]);
  return [ask, () => setAsk(false)] as const;
}

function Arena() {
  const insets = useSafeAreaInsets(), tab = useArenaTab(), router = useRouter(), reduced = useReducedMotion();
  const uid = useAuth().user?.id || "", daily = useDaily(uid), look = useDailyLook();
  const [ask, done] = useDailyOffer();
  const offer = ask && !!daily.data && daily.data.you.status !== "done" && tab === "arena";
  // Analytics: the Store, the Trophy tab's leagues and the Gang tab, each time one is opened.
  useFocusEffect(useCallback(() => { enterFeature(tab === "store" ? "store" : tab === "trophy" ? "leagues" : tab === "gang" ? "gangs" : ""); }, [tab]));
  // Warm the Trophy and Gang lists while the lobby is open, so those tabs open with their data in one go (no spinner, no jump).
  useEffect(() => {
    if (!uid) return;
    prefetch(`u.${uid}.rfboard.JEE`, () => rf("/leaderboard?exam=JEE", uid), false);
    prefetch(`u.${uid}.rffeed`, () => rf("/feed", uid), false);
    prefetch(`u.${uid}.rfcode`, () => rf("/friends/code", uid));
  }, [uid]);
  // Phone Back: Trophy, Gang and Store return to the lobby; the lobby returns to Home.
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { if (tab === "arena") return false; setArenaTab("arena"); return true; });
    return () => sub.remove();
  }, [tab]));
  return <ArenaBg testID="arena-screen">
    <View style={[styles.body, { paddingTop: insets.top + 6 }]}>
      <TopStrip />
      <View style={styles.banner}><ChallengeBanner /></View>
      {/* Each tab comes in with one soft fade, once: its lists never pop in row by row. */}
      <Animated.View key={tab} entering={reduced ? undefined : FadeIn.duration(200)} style={styles.flex}>
        {tab === "arena" ? <LobbyTab /> : tab === "trophy" ? <TrophyTab /> : tab === "gang" ? <GangTab /> : <StoreTab />}
      </Animated.View>
    </View>
    <ArenaBar />
    <DailyPopup visible={offer} d={daily.data} look={look} onExit={done} onEnter={() => { done(); router.push(go.daily()); }} />
  </ArenaBg>;
}

const styles = StyleSheet.create({ body: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" }, banner: { paddingHorizontal: 12 }, flex: { flex: 1 } });
export default withRapid(Arena, { banner: false });

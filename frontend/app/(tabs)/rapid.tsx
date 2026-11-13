import React, { useCallback } from "react";
import { BackHandler, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { withRapid } from "@/src/rapid/ui";
import { ArenaBg } from "@/src/rapid/arena";
import { ArenaBar } from "@/src/rapid/ArenaBar";
import { TopStrip } from "@/src/rapid/TopStrip";
import { ChallengeBanner } from "@/src/rapid/ChallengeBanner";
import { LobbyTab } from "@/src/rapid/LobbyTab";
import { TrophyTab } from "@/src/rapid/TrophyTab";
import { GangTab } from "@/src/rapid/GangTab";
import { StoreTab } from "@/src/rapid/StoreTab";
import { setArenaTab, useArenaTab } from "@/src/rapid/social";

// The Crimson Arena: Rapid Fire's own world with its own bottom bar. The app's bar hides while this tab is open.
function Arena() {
  const insets = useSafeAreaInsets(), tab = useArenaTab();
  // Phone Back: Trophy, Gang and Store return to the lobby; the lobby returns to Home.
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { if (tab === "arena") return false; setArenaTab("arena"); return true; });
    return () => sub.remove();
  }, [tab]));
  return <ArenaBg testID="arena-screen">
    <View style={[styles.body, { paddingTop: insets.top + 6 }]}>
      <TopStrip />
      <View style={styles.banner}><ChallengeBanner /></View>
      {tab === "arena" ? <LobbyTab /> : tab === "trophy" ? <TrophyTab /> : tab === "gang" ? <GangTab /> : <StoreTab />}
    </View>
    <ArenaBar />
  </ArenaBg>;
}

const styles = StyleSheet.create({ body: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" }, banner: { paddingHorizontal: 12 } });
export default withRapid(Arena, { banner: false });

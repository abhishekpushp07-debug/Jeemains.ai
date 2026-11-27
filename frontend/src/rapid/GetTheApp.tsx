// The browser copy of Rapid Fire (src/arenaMode.ts) exists for one person: a friend who opened a match link without
// the app (owner, 28 Nov 2026: "Rapid Fire is just an app thing… browser version bas friends without app ko link ke
// liye hai"). At the very end of the result, one big card takes that friend to the app, in their own phone's store
// ("app download krne ka just at the end with result bda card me… ekdum app jaisa"). Never shown in the app itself.
// The store addresses come from the app's server (GET /api/app/switches "stores"), so the iPhone one can be added
// the day the iPhone app is in the App Store, without building this copy again.
import React, { useEffect, useState } from "react";
import { Image, Linking, StyleSheet, View } from "react-native";
import { appSwitches, askSwitches, onAppSwitches } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Twinkles } from "./juice";

const ROCKET = require("../../assets/arena/em_rocket.webp");
const POINTS = ["All India battle every day, with its leaderboard", "Gangs, Cups and Match Rooms with friends", "Coins, diamonds and your daily streak"];

const agent = typeof navigator !== "undefined" ? navigator.userAgent || "" : "";
// An iPad that calls itself a Mac still has a touch screen.
const IPHONE = /iPhone|iPad|iPod/.test(agent) || (/Macintosh/.test(agent) && typeof document !== "undefined" && "ontouchend" in document);
const ANDROID = /Android/.test(agent);

const link = (v: unknown) => (typeof v === "string" && /^https:\/\//.test(v) ? v : "");

export function GetTheApp() {
  const [stores, setStores] = useState(() => (appSwitches() as any)?.stores);
  useEffect(() => {
    if (!ARENA) return;
    void askSwitches();
    return onAppSwitches(() => setStores((appSwitches() as any)?.stores));
  }, []);
  if (!ARENA) return null;
  const play = link(stores?.android), apple = link(stores?.ios);
  const open = (url: string) => { void Linking.openURL(url).catch(() => {}); };
  const showPlay = !!play && !IPHONE, showApple = !!apple && !ANDROID;
  return <Panel gold sparkles={5} testID="arena-get-app" style={styles.card}>
    <View style={styles.art}>
      <Image source={ROCKET} style={styles.rocket} resizeMode="contain" accessible={false} />
      <Twinkles spots={[[18, 24, 14], [82, 20, 12], [50, 6, 10], [12, 76, 10], [88, 72, 12]]} />
    </View>
    <T w="heavy" size={11} color={arena.aqua} style={styles.center}>YOU PLAYED IN THE BROWSER</T>
    <GoldTitle size={28} center testID="arena-get-app-title">PLAY IN THE APP</GoldTitle>
    <T w="bold" size={13} color={arena.text} style={styles.center}>The full Rapid Fire lives in the JEELIVE.AI app. Free.</T>
    <View style={styles.points}>
      {POINTS.map((p) => <View key={p} style={styles.point}>
        <T w="heavy" size={14} color={arena.gold}>✓</T>
        <T w="bold" size={13} color={arena.text} style={styles.flex}>{p}</T>
      </View>)}
    </View>
    {showPlay ? <RaisedButton testID="arena-get-app-android" glyph="google-play" height={60} streak label="GOOGLE PLAY" sub="Get the app · Android phones" onPress={() => open(play)} style={styles.button} /> : null}
    {showApple ? <RaisedButton testID="arena-get-app-ios" glyph="apple" height={60} streak={!showPlay} tone={showPlay ? "wine" : undefined} label="APP STORE" sub="Get the app · iPhone and iPad" onPress={() => open(apple)} style={styles.button} /> : null}
    {!apple && !ANDROID && (play || IPHONE) ? <T testID="arena-get-app-ios-soon" w="bold" size={12} color={arena.muted} style={styles.center}>
      {IPHONE ? "The iPhone app is coming soon. Till then, play right here in the browser." : "iPhone app coming soon."}</T> : null}
    {!play && !apple && !IPHONE ? <T testID="arena-get-app-soon" w="bold" size={12} color={arena.muted} style={styles.center}>The app link is on its way. Till then, play right here.</T> : null}
  </Panel>;
}

const styles = StyleSheet.create({
  card: { alignItems: "center", gap: 8, paddingVertical: 20, paddingHorizontal: 16 },
  art: { width: 120, height: 104, alignItems: "center", justifyContent: "center" },
  rocket: { width: 96, height: 96 },
  center: { textAlign: "center" },
  points: { alignSelf: "stretch", gap: 6, marginVertical: 4 },
  point: { flexDirection: "row", alignItems: "center", gap: 10 },
  flex: { flex: 1, minWidth: 0 },
  button: { alignSelf: "stretch" },
});

import React, { useCallback, useEffect, useState } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle } from "./arena";
import { Jelly, LiveDot } from "./juice";
import { CupNight, countdown, go, useCupNight } from "./social";
import { Glitter } from "./Glitter";

/** The Colosseum stands, packed and roaring: the backdrop of Cup Night. */
export const STANDS = require("../../assets/arena/bg_colosseum_stands.webp");

/** The server's clock, ticking every second (the phone's clock may be off). */
export function useServerNow(n?: CupNight | null) {
  const [phone, setPhone] = useState(() => Date.now() / 1000);
  useEffect(() => {
    const iv = setInterval(() => setPhone(Date.now() / 1000), 1000);
    return () => clearInterval(iv);
  }, []);
  return n ? phone + (n.now - n.local) : phone;
}

export type NightKey = "soon" | "doors" | "in" | "drawing" | "mine" | "live" | "over";

/** Where tonight stands at this second: before the doors, doors open, you're in, the draw, your cup, cups live, all done. */
export function nightState(n: CupNight, now: number): { key: NightKey; left: number } {
  const mine = n.cups.find((c) => c.mine);
  if (now < n.doors_ts) return { key: "soon", left: n.doors_ts - now };
  if (now < n.start_ts) return { key: n.joined ? "in" : "doors", left: n.start_ts - now };
  if (n.status !== "seated" && n.count > 0) return { key: "drawing", left: 0 };
  if (mine && mine.status !== "finished") return { key: "mine", left: 0 };
  if (n.cups.some((c) => c.status !== "finished")) return { key: "live", left: 0 };
  return { key: "over", left: n.next_ts - now };
}

const LINES: Record<NightKey, (n: CupNight, left: number) => [string, string, string]> = {
  soon: (n, l) => [`DAILY · ${n.time_label.toUpperCase()}`, `Doors open in ${countdown(l)} · ${n.doors_label}`, "SEE"],
  doors: (n, l) => ["DOORS ARE OPEN", `Starts in ${countdown(l)} · ${n.count} in`, "JOIN"],
  in: (n, l) => ["YOU’RE IN ✓", `Starts in ${countdown(l)} · ${n.count} in`, "OPEN"],
  drawing: (n) => [`${n.time_label.toUpperCase()} · THE DRAW`, "Drawing tonight’s cups…", "OPEN"],
  mine: () => ["YOUR CUP IS ON", "Your match is waiting. Go!", "PLAY"],
  live: (n) => ["LIVE NOW", `${n.cups.length} cup${n.cups.length === 1 ? "" : "s"} · ${n.count} students`, "WATCH"],
  over: (n, l) => [n.cups.length ? "CHAMPIONS CROWNED" : "DAILY CUP", `Next one in ${countdown(l)}`, "SEE"],
};

/**
 * Cup Night on the lobby: a free Open Cup every day at 8 pm, with the countdown, how many have joined, and one tap to
 * join, play your match or watch. The answer is fetched again as each moment of the night arrives.
 */
export function CupNightBanner({ uid, testID = "rf-cup-night" }: { uid: string; testID?: string }) {
  const router = useRouter(), narrow = useWindowDimensions().width < 360; // small phones: a smaller trophy leaves room for the countdown
  const q = useCupNight(uid), n = q.data, reload = q.reload;
  const now = useServerNow(n);
  useFocusEffect(useCallback(() => {
    reload();
    const iv = setInterval(reload, 20000 + Math.random() * 5000);
    return () => clearInterval(iv);
  }, [reload]));
  const s = n ? nightState(n, now) : null, key = s?.key;
  useEffect(() => { if (key) reload(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (key !== "drawing") return;
    const iv = setInterval(reload, 3000 + Math.random() * 2000);
    return () => clearInterval(iv);
  }, [key, reload]);
  if (!n || !s) return null;
  const [kicker, line, cta] = LINES[s.key](n, s.left);
  const mine = n.cups.find((c) => c.mine), hot = s.key === "mine" || s.key === "live" || s.key === "drawing";
  return <Jelly testID={testID} accessibilityLabel={`Cup Night. ${kicker}. ${line}`} onPress={() => router.push(s.key === "mine" && mine ? go.cup(mine.id) : go.night())}>
    <Glitter radius={22} inner={styles.face}>
      <Image source={STANDS} style={StyleSheet.absoluteFill} contentFit="cover" contentPosition="center" />
      <LinearGradient pointerEvents="none" colors={[arena.scrim, arena.shade, arena.scrim]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} />
      <Alive kind="breathe"><GameIcon name="trophy" size={narrow ? 44 : 58} /></Alive>
      <View style={styles.flex}>
        <View style={styles.kick}>{hot ? <LiveDot size={8} /> : null}<T testID={`${testID}-kicker`} w="heavy" size={10.5} color={hot ? arena.danger : arena.aqua} style={styles.spaced} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>{kicker}</T></View>
        <GoldTitle size={narrow ? 20 : 22}>Cup Night</GoldTitle>
        <T testID={`${testID}-line`} w="bold" size={12} color={arena.text} numberOfLines={2}>{line}</T>
      </View>
      <View style={[styles.go, narrow && styles.goNarrow, s.key === "doors" || s.key === "mine" ? styles.goHot : null]}><T w="heavy" size={13} color={arena.text}>{cta}</T></View>
    </Glitter>
  </Jelly>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0, gap: 1 }, spaced: { letterSpacing: 1.2, flexShrink: 1 },
  face: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 92, paddingHorizontal: 12, paddingVertical: 10, borderBottomWidth: 4, borderBottomColor: arena.goldDeep },
  kick: { flexDirection: "row", alignItems: "center", gap: 5 },
  go: { height: 44, paddingHorizontal: 12, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.rimHi, borderBottomWidth: 4, borderBottomColor: arena.panelEdge },
  goNarrow: { paddingHorizontal: 9 },
  goHot: { backgroundColor: arena.teal, borderColor: arena.tealOutline, borderBottomColor: arena.tealDeep },
});

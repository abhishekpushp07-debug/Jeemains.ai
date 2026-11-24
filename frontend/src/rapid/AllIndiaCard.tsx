import React, { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import Animated, { css } from "react-native-reanimated";
import { useStill } from "@/src/motion";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, T } from "@/src/components/ui";
import { allIndia, arena } from "@/src/theme";
import { GoldTitle } from "./arena";
import { Glitter } from "./Glitter";
import { Jelly, LiveDot } from "./juice";
import { firstToday, playSfx } from "@/src/sfx";
import { DailyScene, SCENE_SOUND } from "./DailyScenes";
import { DAILY_CARDS, DailyLook, DailyStatus, grouped, hms, useEndsIn } from "./daily";

/** The All India Rapid trophy (original artwork: a golden globe with India lit up, held by two flames). */
export const TROPHY = require("../../assets/arena/daily_trophy.webp");

const SHINE = css.keyframes({ "0%": { transform: [{ translateX: -140 }, { rotate: "18deg" }] }, "55%": { transform: [{ translateX: 560 }, { rotate: "18deg" }] }, "100%": { transform: [{ translateX: 560 }, { rotate: "18deg" }] } });

/** Play a scene's sound now (the styles page uses it as a preview). */
export const playScene = (look: DailyLook) => playSfx(SCENE_SOUND[look], 0.85);

function copy(d?: DailyStatus | null) {
  const you = d?.you, total = d?.total || DAILY_CARDS;
  if (!d) return { title: "All India Rapid", line: `Today’s ${DAILY_CARDS} PCM cards are ready`, cta: "PLAY NOW" };
  if (you?.status === "done") return { title: you.rank ? `#${grouped(you.rank)} in India` : "Done for today", line: `${you.correct}/${total} · ${grouped(d.players)} played today`, cta: "SEE ALL INDIA BOARD" };
  if (you?.status === "playing") return { title: "Your round is on", line: `Card ${(you.i || 0) + 1} of ${total} · the clock is running`, cta: "CONTINUE" };
  return { title: "Play for #1 in India", line: `${total} PCM cards · ${d.seconds} s each · ${d.players ? `${grouped(d.players)} played` : "be the first!"}`, cta: "PLAY NOW" };
}

/**
 * The All India Rapid card: one big square on the lobby. The whole card is the button (straight to the questions).
 * Five living scenes in one fire world; the story on it (players today, your rank, today's #1, the countdown) is the same in each.
 */
export function AllIndiaCard({ d, look = 2, size, onPress, onLongPress, paused, sound, testID = "rf-all-india" }: { d?: DailyStatus | null; look?: DailyLook; size: number; onPress?: () => void; onLongPress?: () => void; paused?: boolean; sound?: boolean; testID?: string }) {
  const still = useStill() || !!paused;
  useEffect(() => { // the card's sound greets the student once a day: the first time it appears (popup or lobby)
    if (!sound) return;
    let on = true;
    const t = setTimeout(() => { void firstToday("card", () => on).then((first) => { if (first) playScene(look); }); }, 450);
    return () => { on = false; clearTimeout(t); };
  }, [sound, look]);
  const left = useEndsIn(d?.ends_in), c = copy(d);
  const champ = d?.top?.[0] && d.you.status !== "done" ? `Today’s #1: ${d.top[0].you ? "You" : d.top[0].name} · ${d.top[0].correct}/${d.total}`
    : d?.yesterday?.[0] ? `Yesterday’s champion: ${d.yesterday[0].you ? "You" : d.yesterday[0].name} · ${d.yesterday[0].correct}/${d.total}` : `Physics · Chemistry · Maths · same ${d?.total || DAILY_CARDS} for all India`;
  const inner = size - 5, done = d?.you.status === "done";
  return <Jelly testID={testID} onPress={onPress} onLongPress={onLongPress} accessibilityLabel={`All India Rapid. ${c.title}. ${c.line}. ${c.cta}`} style={{ width: size, alignSelf: "center" }}>
    <Glitter radius={28} ring={2.5} sparkles={4} inner={{ width: inner, height: inner, backgroundColor: allIndia.ink }}>
      <DailyScene look={look} size={inner} still={still} />
      <LinearGradient pointerEvents="none" colors={[arena.clear, arena.scrim]} locations={[0.5, 0.84]} style={StyleSheet.absoluteFill} />

      <View style={styles.chips}>
        <View style={styles.chip}><LiveDot size={7} /><T testID={`${testID}-players`} w="heavy" size={10.5} color={arena.text} numberOfLines={1}>{d?.players ? `LIVE · ${grouped(d.players)}` : "LIVE"}</T></View>
        <View style={styles.chip}><Icon name="timer-sand" size={13} color={arena.gold} /><T testID={`${testID}-clock`} w="heavy" size={10.5} color={arena.gold}>{d ? hms(left) : "--:--:--"}</T></View>
      </View>

      <View style={styles.foot}>
        <T w="heavy" size={10.5} color={allIndia.hot} style={styles.kicker} numberOfLines={1}>ALL INDIA RAPID FIRE · TODAY</T>
        <GoldTitle size={size < 330 ? 22 : 26} testID={`${testID}-title`}>{c.title}</GoldTitle>
        <T testID={`${testID}-line`} w="bold" size={12} color={arena.text} numberOfLines={1}>{c.line}</T>
        <T testID={`${testID}-champ`} w="bold" size={11} color={arena.muted} numberOfLines={1}>{champ}</T>
        <View style={[styles.cta, done && styles.ctaDone]}>
          <LinearGradient pointerEvents="none" colors={done ? [arena.gold, arena.goldDeep] : [arena.tealHi, arena.teal]} style={StyleSheet.absoluteFill} />
          {still ? null : <Animated.View pointerEvents="none" style={[styles.shine, { animationName: SHINE, animationDuration: 3600, animationIterationCount: "infinite", animationTimingFunction: "ease-in-out" }]}><LinearGradient colors={[arena.clear, arena.sheen, arena.clear]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} /></Animated.View>}
          <Icon name={done ? "trophy" : "lightning-bolt"} size={18} color={done ? arena.badgeInk : arena.text} />
          <T testID={`${testID}-cta`} w="heavy" size={15} color={done ? arena.badgeInk : arena.text} style={styles.ctaText}>{c.cta}</T>
        </View>
      </View>
    </Glitter>
  </Jelly>;
}

const styles = StyleSheet.create({
  chips: { position: "absolute", top: 12, left: 12, right: 12, flexDirection: "row", justifyContent: "space-between" },
  chip: { flexDirection: "row", alignItems: "center", gap: 5, height: 28, paddingHorizontal: 10, borderRadius: 14, backgroundColor: arena.scrim, borderWidth: 1, borderColor: arena.rim },
  foot: { position: "absolute", left: 14, right: 14, bottom: 14, alignItems: "center", gap: 2 },
  kicker: { letterSpacing: 1.6, textShadowColor: arena.black, textShadowRadius: 6, textShadowOffset: { width: 0, height: 1 } },
  cta: { alignSelf: "stretch", marginTop: 8, height: 48, borderRadius: 16, overflow: "hidden", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  ctaDone: { borderColor: arena.goldDeep, borderBottomColor: arena.goldDeep },
  ctaText: { letterSpacing: 1.5 },
  shine: { position: "absolute", top: -30, bottom: -30, width: 56, left: 0 },
});

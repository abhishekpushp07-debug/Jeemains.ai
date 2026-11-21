import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { rf, uuid } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle } from "./arena";
import { Glitter } from "./Glitter";
import { Jelly } from "./juice";
import { CARD_SECONDS, useCardCount } from "./scope";

// Weak Topic Sprint: a 20-second sprint dealt only from the subtopics this student keeps missing.
export type WeakTopic = { subject: string; chapter: string; topic: string; misses: number; tries: number; missed: number };
export type WeakTopics = { exam: string; cards: number; seconds: number; topics: WeakTopic[]; rule: string };
export const useWeakTopics = (uid?: string) => useCached<WeakTopics>(uid ? `u.${uid}.rfweaktopics.JEE` : null, () => rf("/weak-topics?exam=JEE", uid!), false);

/** Starts the sprint with the student's chosen card count. Shared by the lobby strip and the Weak cards sheet. */
export function useSprintStart() {
  const router = useRouter(), n = useCardCount();
  return () => router.push({ pathname: "/rapid/session", params: { exam: "JEE", weak: "1", n: String(n), r: uuid() } });
}
const names = (t: WeakTopic[]) => t.slice(0, 2).map((x) => x.topic).join(", ") + (t.length > 2 ? ` +${t.length - 2} more` : "");

/** The lobby strip: one tap starts the sprint. Before any misses it says how it builds itself. */
export function WeakSprintStrip({ uid, narrow }: { uid: string; narrow?: boolean }) {
  const start = useSprintStart(), q = useWeakTopics(uid), topics = q.data?.topics || [], n = useCardCount();
  const ready = topics.length > 0, compact = useWindowDimensions().width < 400; // phones up to 400 px: smaller art and title
  return <Jelly testID="rf-weak-sprint" disabled={!ready} onPress={start} accessibilityLabel={ready ? `Weak Topic Sprint. ${topics.length} subtopics you often miss. Start` : "Weak Topic Sprint. Builds itself as you play"}>
    <Glitter radius={22} inner={styles.inner}><LinearGradient colors={[arena.panelHi, arena.panel]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.face}>
      <Alive kind="breathe"><GameIcon name="target" size={compact ? 44 : 58} /></Alive>
      <View style={styles.flex}>
        <T w="heavy" size={narrow ? 10 : 11} color={arena.aqua} style={styles.kicker} numberOfLines={1}>ONLY YOUR MISSES</T>
        <GoldTitle size={narrow ? 15 : compact ? 16 : 19} lines={1}>Weak Topic Sprint</GoldTitle>
        <T testID="rf-weak-sprint-line" w="bold" size={narrow ? 10.5 : 11.5} color={arena.text} numberOfLines={1}>
          {ready ? `${topics.length} subtopic${topics.length > 1 ? "s" : ""} · ${Math.min(n, q.data!.cards)} cards · ${CARD_SECONDS} s` : q.data ? "Builds itself from the cards you miss" : "Finding your weak subtopics…"}
        </T>
        {ready ? <T testID="rf-weak-sprint-names" w="bold" size={narrow ? 10 : 11} color={arena.muted} numberOfLines={1}>{names(topics)}</T> : null}
      </View>
      <View style={[styles.go, !ready && styles.goOff]}><T testID="rf-weak-sprint-cta" w="heavy" size={13} color={arena.text}>{ready ? "START" : "SOON"}</T></View>
    </LinearGradient></Glitter>
  </Jelly>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0, gap: 1 }, kicker: { letterSpacing: 1.5 },
  inner: { borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  face: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 88, paddingHorizontal: 14, paddingVertical: 10, overflow: "hidden" },
  go: { height: 44, paddingHorizontal: 12, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  goOff: { backgroundColor: arena.panelHi, borderColor: arena.rim, borderBottomColor: arena.panelEdge },
});

import React, { useCallback } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Pop } from "./juice";
import { Crown, Face } from "./parts";
import { CrownArt } from "./CrownArt";
import { Champion, go, useChampions } from "./social";

/** One champion on the wall: their crown over their face, the cup they won, and the Cheer button. */
function ChampCard({ c, i, onCheer }: { c: Champion; i: number; onCheer: () => void }) {
  const gold = (c.crown?.real || 0) > 0;
  return <Pop delay={i * 70}>
    <View testID={`rf-champ-${c.pid}`} style={[styles.card, c.you && styles.cardYou]}>
      <Alive kind="float" delay={i * 300}><CrownArt size={44} gold={gold} /></Alive>
      <Face p={c} size={58} />
      <T w="heavy" size={13} color={arena.text} numberOfLines={1} style={styles.center}>{c.you ? "You!" : c.name}</T>
      <View style={styles.inline}><Crown c={c.crown} /><T w="bold" size={10.5} color={arena.muted} numberOfLines={1}>Cup {c.no} · {c.size}</T></View>
      <RaisedButton testID={`rf-champ-${c.pid}-cheer`} glyph="party-popper" height={40} label="CHEER" onPress={onCheer} style={styles.stretch} />
    </View>
  </Pop>;
}

/**
 * Champions Wall in the lobby: the last Cup Night's champions, from the moment they are crowned until the next night's
 * doors open. Cheer one and their cheer squad dances in their trophy cabinet.
 */
export function ChampionsWall({ uid }: { uid: string }) {
  const router = useRouter();
  const q = useChampions(uid), reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const d = q.data, items = d?.items || [];
  if (!d?.day || !items.length) return null;
  return <Panel gold testID="rf-champions-wall" style={styles.wall}>
    <LinearGradient pointerEvents="none" colors={[arena.goldSoft, arena.clear]} style={StyleSheet.absoluteFill} />
    <View style={styles.head}>
      <Alive kind="breathe"><GameIcon name="trophy" size={44} /></Alive>
      <View style={styles.flex}>
        <T w="heavy" size={10.5} color={arena.aqua} style={styles.spaced} numberOfLines={1}>CHAMPIONS WALL · CUP NIGHT</T>
        <GoldTitle size={20} testID="rf-champions-title">{d.tonight ? "Tonight’s champions" : "Last night’s champions"}</GoldTitle>
      </View>
      <View style={styles.count}><T testID="rf-champions-count" w="heavy" size={13} color={arena.badgeInk}>{items.length}</T></View>
    </View>
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row} testID="rf-champions-list">
      {items.map((c, i) => <ChampCard key={c.cup_id} c={c} i={i} onCheer={() => router.push(go.cheer(c.pid))} />)}
    </ScrollView>
    <T w="bold" size={11} color={arena.muted} style={styles.center}>Tap Cheer and their cheer squad dances in the trophy cabinet. Next Cup Night at {d.time_label}.</T>
  </Panel>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 1.5 }, stretch: { alignSelf: "stretch" },
  inline: { flexDirection: "row", alignItems: "center", gap: 4 },
  wall: { padding: 12, gap: 10, overflow: "hidden" },
  head: { flexDirection: "row", alignItems: "center", gap: 10 },
  count: { minWidth: 30, height: 30, paddingHorizontal: 8, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  row: { gap: 10, paddingRight: 4 },
  card: { width: 124, alignItems: "center", gap: 4, paddingHorizontal: 8, paddingTop: 4, paddingBottom: 10, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.goldDeep },
  cardYou: { borderColor: arena.gold, backgroundColor: arena.panelHi },
});

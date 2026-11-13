import React from "react";
import { StyleSheet, View } from "react-native";
import Animated, { ZoomIn, useReducedMotion } from "react-native-reanimated";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { Jelly, Pop } from "./juice";
import { RivalGem, StreakGem } from "./StreakGem";
import { ordinal } from "./social";

export type MatchPlayer = {
  you: boolean; bot?: boolean; name: string; avatar?: string | null; frame?: string | null; entry?: string | null; pid?: string | null;
  level?: number; wins?: number; score: number; answered: number; rank: number; done?: boolean; forfeit?: boolean; streak?: number; answers?: { outcome: string; choice?: number | null }[];
};
export const shownName = (p?: Partial<MatchPlayer> | null) => (p?.you ? "You" : p?.name || "Rival");

function Side({ p, total, right }: { p?: MatchPlayer; total: number; right?: boolean }) {
  const reduced = useReducedMotion();
  return <View style={[styles.side, right && styles.end]}>
    <View style={[styles.who, right && styles.reverse]}>
      <Avatar icon={p?.avatar} frame={p?.frame} size={36} />
      <View style={[styles.flex, right && styles.end]}>
        <T w="heavy" size={12} color={p?.you ? arena.gold : arena.text} numberOfLines={1}>{shownName(p)}</T>
        {p?.bot ? <T testID="duel-practice-rival-label" w="bold" size={10} color={arena.aqua}>Practice rival</T> : null}
      </View>
    </View>
    <View style={[styles.scoreRow, right && styles.reverse]}>
      <Animated.View key={p?.score ?? 0} entering={reduced ? undefined : ZoomIn.duration(220)}>
        <T testID={right ? "duel-opp-score" : "duel-my-score"} w="heavy" size={30} color={right ? arena.text : arena.gold}>{p?.score ?? 0}</T>
      </Animated.View>
      {/* The rival's live Phoenix streak: the diamond they are burning right now. */}
      {right && !p?.forfeit ? <RivalGem streak={p?.streak || 0} size={22} testID="duel-opp-streak" /> : null}
    </View>
    <View style={[styles.track, right && styles.end]}>
      <View style={[styles.fill, { width: `${Math.min(1, (p?.answered || 0) / total) * 100}%`, backgroundColor: right ? arena.rimHi : arena.tealHi }]} />
    </View>
    <T w="bold" size={10} color={arena.muted}>{p?.answered || 0}/{total} cards</T>
  </View>;
}

/** Live scores above the card. 1 v 1: both sides with progress. 3 to 5 players: everyone in live rank order, you in gold, with your place. */
export function ScoreStrip({ players, total, streak }: { players: MatchPlayer[]; total: number; streak?: number | null }) {
  const me = players.find((p) => p.you), opp = players.find((p) => !p.you);
  if (players.length > 2) {
    const ranked = [...players].sort((a, b) => a.rank - b.rank);
    return <View testID="duel-versus" style={styles.strip}>
      <View style={styles.cells}>
        {ranked.map((p, i) => <View key={p.pid || i} testID={p.you ? "duel-cell-you" : `duel-cell-${i}`} style={[styles.cell, p.you && styles.cellYou, p.forfeit && styles.gone]}>
          <Avatar icon={p.avatar} frame={p.frame} size={30} />
          <T w="heavy" size={10} color={p.you ? arena.gold : arena.muted} numberOfLines={1}>{shownName(p)}</T>
          <T testID={p.you ? "duel-my-score" : undefined} w="heavy" size={17} color={p.you ? arena.gold : arena.text}>{p.score}</T>
          {!p.you && !p.forfeit ? <View style={styles.cellGem}><RivalGem streak={p.streak || 0} size={15} testID={`duel-cell-streak-${i}`} /></View> : null}
        </View>)}
      </View>
      <View style={styles.foot}>
        <T testID="duel-place" w="heavy" size={14} color={arena.gold}>{ordinal(me?.rank || 1)} / {players.length}</T>
        {streak != null ? <StreakGem streak={streak} /> : null}
      </View>
    </View>;
  }
  const lead = (me?.score ?? 0) - (opp?.score ?? 0);
  return <View testID="duel-versus" style={styles.strip}>
    <View style={styles.duo}>
      <Side p={me} total={total} />
      {streak != null ? <StreakGem streak={streak} /> : <View style={styles.vs}><T w="heavy" size={13} color={arena.badgeInk}>VS</T></View>}
      <Side p={opp} total={total} right />
    </View>
    {opp && !opp.forfeit ? <T testID="duel-lead" w="heavy" size={12} color={lead > 0 ? arena.online : lead < 0 ? arena.danger : arena.gold} style={styles.center}>
      {lead > 0 ? `You lead by ${lead}. Keep it up!` : lead < 0 ? `Behind by ${-lead}. Push harder!` : "Neck and neck!"}
    </T> : null}
  </View>;
}

/** Everyone seated in a row (before card 1 and while waiting for the others to finish). */
export function Lineup({ players }: { players: MatchPlayer[] }) {
  const size = players.length > 3 ? 48 : 60;
  return <View testID="duel-lineup" style={styles.lineup}>
    {players.map((p, i) => <View key={p.pid || i} style={[styles.seat, { width: size + 14 }]}>
      <Avatar icon={p.avatar} frame={p.frame} size={size} />
      <T w="heavy" size={11} color={p.you ? arena.gold : arena.text} numberOfLines={1}>{shownName(p)}</T>
    </View>)}
  </View>;
}

const STEP = [92, 66, 48];
/** 1st, 2nd and 3rd of a 3 to 5 player match. Tapping a player opens their profile. */
export function Podium({ players, onOpen }: { players: MatchPlayer[]; onOpen?: (pid: string) => void }) {
  const top = [...players].sort((a, b) => a.rank - b.rank).slice(0, 3);
  const order = [top[1], top[0], top[2]].filter(Boolean);
  return <View testID="duel-podium" style={styles.podium}>
    {order.map((p) => {
      const first = p.rank === 1;
      const face = <Avatar icon={p.avatar} frame={p.frame} size={first ? 66 : 50} />;
      return <Pop key={p.rank} delay={(3 - p.rank) * 220} style={styles.step}>
        {onOpen && p.pid && !p.you ? <Jelly testID={`duel-podium-open-${p.rank}`} accessibilityLabel={`${p.name}, open profile`} onPress={() => onOpen(p.pid!)}>{face}</Jelly> : face}
        <T w="heavy" size={12} color={p.you ? arena.gold : arena.text} numberOfLines={1}>{shownName(p)}</T>
        <View testID={`duel-podium-${p.rank}`} style={[styles.block, { height: STEP[p.rank - 1] }, first && styles.blockGold]}>
          <T w="heavy" size={first ? 20 : 16} color={first ? arena.badgeInk : arena.gold}>{ordinal(p.rank)}</T>
          <T w="heavy" size={13} color={first ? arena.badgeInk : arena.text}>{p.score}</T>
        </View>
      </Pop>;
    })}
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, end: { alignItems: "flex-end" }, reverse: { flexDirection: "row-reverse" }, center: { textAlign: "center" },
  strip: { alignSelf: "stretch", gap: 6 },
  duo: { flexDirection: "row", alignItems: "center", gap: 8, padding: 10, borderRadius: 20, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  side: { flex: 1, minWidth: 0, gap: 3 }, who: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "stretch" },
  track: { height: 6, alignSelf: "stretch", borderRadius: 3, backgroundColor: arena.panelEdge, overflow: "hidden" }, fill: { height: "100%", borderRadius: 3 },
  vs: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 2, borderColor: arena.goldDeep },
  cells: { flexDirection: "row", gap: 6 },
  cell: { flex: 1, minWidth: 0, alignItems: "center", gap: 1, paddingVertical: 6, paddingHorizontal: 2, borderRadius: 14, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  cellYou: { borderColor: arena.gold, backgroundColor: arena.panelHi }, gone: { opacity: 0.45 },
  scoreRow: { flexDirection: "row", alignItems: "center", gap: 6 }, cellGem: { position: "absolute", top: 2, right: 3 },
  foot: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 4 },
  lineup: { flexDirection: "row", justifyContent: "center", gap: 10, alignSelf: "stretch" }, seat: { alignItems: "center", gap: 4 },
  podium: { flexDirection: "row", alignItems: "flex-end", justifyContent: "center", gap: 10, alignSelf: "stretch" },
  step: { flex: 1, maxWidth: 112, alignItems: "center", gap: 4 },
  block: { alignSelf: "stretch", alignItems: "center", justifyContent: "center", borderTopLeftRadius: 14, borderTopRightRadius: 14, backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.rim },
  blockGold: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});

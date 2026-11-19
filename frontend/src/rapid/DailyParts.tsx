import React, { useEffect } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { RewardPanel } from "@/src/components/game";
import { arena } from "@/src/theme";
import { Alive } from "./Art";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Confetti, Twinkles } from "./juice";
import { Face, NameLine, Note } from "./parts";
import { TROPHY } from "./AllIndiaCard";
import { DailyResult, DailyRow, grouped, secs, useDailyBoard } from "./daily";
import { go } from "./social";

const MEDAL = [arena.gold, "#D8DEE9", "#E0A36B"];

/** Today's All India board: rank, player, cards right and the time taken (the tie-break). */
export function DailyBoardList({ items, total, testID = "rf-daily-board" }: { items: DailyRow[]; total: number; testID?: string }) {
  const router = useRouter();
  return <Panel testID={testID} sparkles={4} style={styles.board}>
    <GoldTitle size={18}>All India board · today</GoldTitle>
    {items.map((r) => <View key={r.rank} testID={`${testID}-row-${r.rank}`} style={[styles.row, r.you && styles.rowYou]}>
      <View style={[styles.medal, r.rank <= 3 && { backgroundColor: MEDAL[r.rank - 1], borderColor: arena.badgeInk }]}><T w="heavy" size={12} color={r.rank <= 3 ? arena.badgeInk : arena.muted}>{r.rank}</T></View>
      <Face p={r} size={36} onPress={r.pid ? () => router.push(go.player(r.pid!)) : undefined} />
      <View style={styles.flex}><NameLine name={`${r.name}${r.you ? " (you)" : ""}`} crown={r.crown} size={14} /><T w="bold" size={11} color={arena.muted}>Level {r.level}</T></View>
      <View style={styles.score}><T w="heavy" size={14} color={arena.gold}>{r.correct}/{total}</T><T w="bold" size={10.5} color={arena.muted}>{secs(r.ms)}</T></View>
    </View>)}
    {!items.length ? <Note>Nobody on today’s board yet.</Note> : null}
    <T size={10} color={arena.faint} style={styles.center}>Most cards right wins; on a tie, the faster total time. Practice, not exam ranks.</T>
  </Panel>;
}

/** After the 30th card: your All India rank, the score, the reward and today's board. */
export function DailyResultView({ result, uid, onBack }: { result: DailyResult; uid: string; onBack: () => void }) {
  const board = useDailyBoard(uid), reload = board.reload;
  const art = Math.min(useWindowDimensions().width * 0.46, 200);
  useEffect(() => { reload(); }, [reload, result.rank]);
  const top = (result.rank || 999) <= 10;
  return <ScrollView testID="rf-daily-result" contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
    {top ? <Confetti /> : null}
    <View style={styles.hero}>
      <Alive kind="breathe"><Image source={TROPHY} contentFit="contain" style={{ width: art, height: art }} accessible={false} /></Alive>
      <Twinkles spots={[[20, 22, 16], [80, 18, 14], [50, 4, 12], [16, 74, 12], [84, 70, 14]]} />
    </View>
    <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>ALL INDIA RAPID FIRE · {result.day}</T>
    <GoldTitle size={34} center testID="rf-daily-rank">{result.rank ? `#${grouped(result.rank)} in India` : "Round complete"}</GoldTitle>
    <T testID="rf-daily-players" w="bold" size={13} color={arena.text} style={styles.center}>of {grouped(result.players)} player{result.players === 1 ? "" : "s"} today</T>
    <View style={styles.stats}>
      <Panel style={styles.stat}><T w="heavy" size={28} color={arena.gold} testID="rf-daily-score">{result.correct}/{result.total}</T><T w="bold" size={11} color={arena.muted}>cards right</T></Panel>
      <Panel style={styles.stat}><T w="heavy" size={28} color={arena.text} testID="rf-daily-time">{secs(result.ms)}</T><T w="bold" size={11} color={arena.muted}>total time</T></Panel>
    </View>
    {result.reward ? <RewardPanel reward={result.reward} title={top ? "Top 10 in India!" : "All India round done"} /> : null}
    {board.data ? <DailyBoardList items={board.data.items} total={board.data.total} /> : null}
    <T w="bold" size={12} color={arena.muted} style={styles.center}>30 new cards at midnight. Same cards for everyone, one try.</T>
    <RaisedButton testID="rf-daily-back" label="BACK TO RAPID FIRE" height={56} onPress={onBack} />
  </ScrollView>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, kicker: { letterSpacing: 1.6, textAlign: "center" },
  content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 32, gap: 12 },
  hero: { alignSelf: "center" },
  stats: { flexDirection: "row", gap: 10 }, stat: { flex: 1, alignItems: "center", paddingVertical: 12 },
  board: { padding: 12, gap: 8 },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 54, paddingHorizontal: 10, borderRadius: 14, backgroundColor: arena.panelHi },
  rowYou: { borderWidth: 1.5, borderColor: arena.gold },
  medal: { width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  score: { alignItems: "flex-end" },
});

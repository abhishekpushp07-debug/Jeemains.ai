import React, { useEffect, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { RewardPanel } from "@/src/components/game";
import { arena } from "@/src/theme";
import { MotionWhile } from "@/src/motion";
import { Alive } from "./Art";
import { GoldTitle, Panel, RaisedButton, Segment } from "./arena";
import { Confetti, Twinkles } from "./juice";
import { Face, NameLine, Note } from "./parts";
import { TROPHY } from "./AllIndiaCard";
import { BattleVictory } from "./BattleVictory";
import { DailyShare } from "./DailyShare";
import { DailyMisses } from "./DailyMisses";
import { Sheet } from "./ui";
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

/**
 * After the last card, in two tabs. Result: your All India rank, the score, the reward and today's board. Misfires: the
 * cards you did not get right, with the right answers (asked from the server the first time the tab is opened).
 * `fresh` = the round ended just now; a finished round opened again shows its reward quietly (no coin sound, no level-up show).
 */
export function DailyResultView({ result, uid, onBack, fresh }: { result: DailyResult; uid: string; onBack: () => void; fresh: boolean }) {
  const board = useDailyBoard(uid), reload = board.reload;
  const width = Math.min(useWindowDimensions().width, 560), art = Math.min(width * 0.46, 200);
  const [sharing, setSharing] = useState(false);
  const [tab, setTab] = useState<"result" | "misses">("result");
  const [opened, setOpened] = useState(false); // the Misfires pane is made the first time it is opened, then only hidden
  useEffect(() => { reload(); }, [reload, result.rank]);
  // The charge and the confetti need at least one card right (a lone 0/30 player is "#1" by default).
  const won = result.correct > 0, top = won && (result.rank || 999) <= 10, battle = won && !!result.rank && result.rank <= 100;
  return <View style={styles.flex}>
    <View style={styles.tabs}>
      <Segment prefix="rf-daily-tab" value={tab} onChange={(t) => { setTab(t); if (t === "misses") setOpened(true); }}
        items={[["result", "Result"], ["misses", `Misfires · ${result.total - result.correct}`]]} />
    </View>
    {/* The result stays in place under the Misfires tab and only rests, so coming back never plays the celebration or the coins again. */}
    <View style={[styles.flex, tab !== "result" && styles.hidden]}><MotionWhile on={tab === "result"}>
    <ScrollView testID="rf-daily-result" contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
    {top ? <Confetti /> : null}
    {/* Top 100 in India: the battleground victory charge. Everyone else: the trophy. */}
    {battle ? <BattleVictory width={width - 32} rank={result.rank!} /> : <View style={styles.hero}>
      <Alive kind="breathe"><Image source={TROPHY} contentFit="contain" style={{ width: art, height: art }} accessible={false} /></Alive>
      <Twinkles spots={[[20, 22, 16], [80, 18, 14], [50, 4, 12], [16, 74, 12], [84, 70, 14]]} />
    </View>}
    <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>ALL INDIA RAPID FIRE · {result.day}</T>
    <GoldTitle size={34} center testID="rf-daily-rank">{result.rank ? `#${grouped(result.rank)} in India` : "Round complete"}</GoldTitle>
    <T testID="rf-daily-players" w="bold" size={13} color={arena.text} style={styles.center}>of {grouped(result.players)} player{result.players === 1 ? "" : "s"} today</T>
    <View style={styles.stats}>
      <Panel style={styles.stat}><T w="heavy" size={28} color={arena.gold} testID="rf-daily-score">{result.correct}/{result.total}</T><T w="bold" size={11} color={arena.muted}>cards right</T></Panel>
      <Panel style={styles.stat}><T w="heavy" size={28} color={arena.text} testID="rf-daily-time">{secs(result.ms)}</T><T w="bold" size={11} color={arena.muted}>total time</T></Panel>
    </View>
    <RaisedButton testID="rf-daily-share-open" glyph="whatsapp" height={58} streak label="SHARE MY RANK" sub="Champion card for WhatsApp" onPress={() => setSharing(true)} />
    {result.reward ? <RewardPanel reward={result.reward} historical={!fresh} title={top ? "Top 10 in India!" : battle ? "Top 100 in India!" : "All India round done"} /> : null}
    {board.data ? <DailyBoardList items={board.data.items} total={board.data.total} /> : null}
    <T w="bold" size={12} color={arena.muted} style={styles.center}>{result.total} new PCM cards at midnight. Same cards for everyone, one try.</T>
    <RaisedButton testID="rf-daily-back" label="BACK TO RAPID FIRE" height={56} onPress={onBack} />
    <Sheet visible={sharing} onClose={() => setSharing(false)} testID="rf-daily-share-sheet"><DailyShare result={result} onBack={() => setSharing(false)} /></Sheet>
    </ScrollView>
    </MotionWhile></View>
    {opened ? <View style={[styles.flex, tab !== "misses" && styles.hidden]}><DailyMisses result={result} uid={uid} /></View> : null}
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, kicker: { letterSpacing: 1.6, textAlign: "center" },
  content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 32, gap: 12 },
  tabs: { paddingHorizontal: 16, paddingBottom: 8 }, hidden: { display: "none" },
  hero: { alignSelf: "center" },
  stats: { flexDirection: "row", gap: 10 }, stat: { flex: 1, alignItems: "center", paddingVertical: 12 },
  board: { padding: 12, gap: 8 },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 54, paddingHorizontal: 10, borderRadius: 14, backgroundColor: arena.panelHi },
  rowYou: { borderWidth: 1.5, borderColor: arena.gold },
  medal: { width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  score: { alignItems: "flex-end" },
});

import React, { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { T, tap } from "@/src/components/ui";
import { useGameProfile } from "@/src/components/game";
import { playSfx } from "@/src/sfx";
import { arena } from "@/src/theme";
import { GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton, Segment } from "./arena";
import { Confetti, Pop } from "./juice";
import { Face, NameLine, Note, crownText } from "./parts";
import { ErrorBox } from "./ui";
import { Crown as CrownT, go, setArenaTab } from "./social";

const MEDAL = [arena.gold, "#D8DEE9", "#E0A36B"];
type Row = { rank: number; pid?: string | null; name: string; avatar?: string | null; frame?: string | null; level: number; you: boolean; xp?: number; wins: number; score?: number; matches?: number; crown?: CrownT | null };
const left = (s: number) => { const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600); return d ? `${d}d ${h}h` : `${h}h ${Math.floor((s % 3600) / 60)}m`; };

/** One ranked row: medal, face, name, and the number that ranks it. */
export function BoardRow({ row, value, sub, testID, i = 0 }: { row: Row; value: string; sub: string; testID: string; i?: number }) {
  const router = useRouter();
  return <Pop delay={Math.min(i, 8) * 40}>
    <Pressable testID={testID} disabled={!row.pid || row.you} onPress={() => { tap(); router.push(go.player(row.pid!)); }} accessibilityRole="button" accessibilityLabel={`Rank ${row.rank}, ${row.name}${crownText(row.crown)}, ${value}`} style={[styles.row, row.you && styles.rowYou]}>
      <View style={[styles.medal, row.rank <= 3 && { backgroundColor: MEDAL[row.rank - 1], borderColor: arena.badgeInk }]}><T w="heavy" size={13} color={row.rank <= 3 ? arena.badgeInk : arena.muted}>{row.rank}</T></View>
      <Face p={row} size={40} />
      <View style={styles.flex}>
        <NameLine name={`${row.name}${row.you ? " (you)" : ""}`} crown={row.crown} size={14} testID={`${testID}-crown`} />
        <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{sub}</T>
      </View>
      <T w="heavy" size={13} color={arena.gold}>{value}</T>
    </Pressable>
  </Pop>;
}

/** Friends League: you and your friends, ranked by this week's XP (Monday to Sunday). Last week's top 3 collect coins. */
export function FriendsLeague({ uid }: { uid: string }) {
  const q = useCached<any>(uid ? `u.${uid}.rfleague.friends` : null, () => rf("/league/friends", uid), false);
  const prof = useGameProfile(uid);
  const [when, setWhen] = useState<"week" | "all">("week"), [busy, setBusy] = useState(false), [error, setError] = useState(""), [won, setWon] = useState(0);
  const reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const d = q.data;
  const claim = async () => {
    setBusy(true); setError("");
    try { const r = await rf<any>("/league/friends/claim", uid, { method: "POST", body: {} }); setWon(r.coins); playSfx("coin"); q.reload(); prof.reload(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  if (!d) return q.error ? <ErrorBox testID="rf-league-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="rf-league-loading" color={arena.aqua} />;
  const rows: Row[] = when === "week" ? d.items : d.all_time;
  return <View testID="rf-friends-league" style={styles.list}>
    <Panel gold style={styles.hero}>
      <GameIcon name="friends" size={52} />
      <View style={styles.flex}>
        <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>FRIENDS LEAGUE · {d.week}</T>
        <GoldTitle size={20}>Race your friends</GoldTitle>
        <T testID="rf-league-ends" w="bold" size={12} color={arena.muted}>Resets in {left(d.ends_in)} · top 3 win {d.prizes.join(" / ")} coins</T>
      </View>
    </Panel>
    {d.last?.items?.length ? <Panel flat testID="rf-league-last" style={styles.last}>
      <T w="heavy" size={12} color={arena.gold}>LAST WEEK’S PODIUM</T>
      <View style={styles.podium}>{d.last.items.map((x: Row) => <View key={x.rank} style={styles.podiumCell}>
        <View style={[styles.medal, { backgroundColor: MEDAL[x.rank - 1], borderColor: arena.badgeInk }]}><T w="heavy" size={12} color={arena.badgeInk}>{x.rank}</T></View>
        <Face p={x} size={x.rank === 1 ? 52 : 42} /><NameLine name={x.you ? "You" : x.name} crown={x.crown} size={11} color={x.you ? arena.gold : arena.text} testID={`rf-league-podium-crown-${x.rank}`} />
        <T w="bold" size={10} color={arena.muted}>{x.xp} XP</T>
      </View>)}</View>
      {d.last.can_claim ? <RaisedButton testID="rf-league-claim" icon="coin" height={52} streak label={`COLLECT ${d.last.prize} COINS`} sub={`You finished ${d.last.rank === 1 ? "1st" : d.last.rank === 2 ? "2nd" : "3rd"}!`} busy={busy} onPress={claim} />
        : d.last.claimed ? <T testID="rf-league-claimed" w="heavy" size={12} color={arena.gold} style={styles.center}>Prize collected ✓</T> : null}
      {won ? <T testID="rf-league-won" w="heavy" size={13} color={arena.online} style={styles.center}>+{won} coins added!</T> : null}
      <ErrorBox testID="rf-league-claim-error" error={error} />
    </Panel> : null}
    <Segment prefix="rf-league-when" value={when} onChange={setWhen} items={[["week", "This week"], ["all", "All time"]]} />
    {!d.friends ? <>
      <Note testID="rf-league-empty">Your league is just you for now. Add friends with their Friend Code and race them every week.</Note>
      <RaisedButton testID="rf-league-add" tone="wine" icon="friends" label="Add friends" onPress={() => setArenaTab("gang")} />
    </> : rows.map((r, i) => <BoardRow key={r.pid || r.rank} i={i} row={r} testID={`rf-league-row-${r.rank}`} value={`${r.xp} XP`} sub={`Level ${r.level} · ${r.wins} win${r.wins === 1 ? "" : "s"}`} />)}
    <T size={10} color={arena.faint} style={styles.center}>Weekly XP from every sprint and match. Practice only, not exam ranks.</T>
    {won ? <Confetti count={28} /> : null}
  </View>;
}

/** Gang War board: the top 100 scorers of every Gang vs Gang battle, all time. */
export function GangWarBoard({ uid }: { uid: string }) {
  const q = useCached<any>(uid ? `u.${uid}.rfleague.gangwar` : null, () => rf("/league/gangwar", uid), false);
  const reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const d = q.data;
  if (!d) return q.error ? <ErrorBox testID="rf-gangwar-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="rf-gangwar-loading" color={arena.aqua} />;
  return <View testID="rf-gangwar-board" style={styles.list}>
    <Panel gold style={styles.hero}>
      <GameIcon name="gang" size={52} />
      <View style={styles.flex}>
        <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>GANG WAR · TOP {d.size}</T>
        <GoldTitle size={20}>Gang War legends</GoldTitle>
        <T testID="rf-gangwar-you" w="bold" size={12} color={arena.muted}>{d.you ? `You: #${d.you.rank} · ${d.you.score} points in ${d.you.matches} war${d.you.matches === 1 ? "" : "s"}` : "Fight a Gang War to get on this board"}</T>
      </View>
    </Panel>
    {d.items.map((r: Row, i: number) => <BoardRow key={r.pid || r.rank} i={i} row={r} testID={`rf-gangwar-row-${r.rank}`} value={`${r.score} pts`} sub={`${r.matches} war${r.matches === 1 ? "" : "s"} · ${r.wins} won`} />)}
    {!d.items.length ? <Note testID="rf-gangwar-empty">No Gang War yet. Open your gang and press GANG WAR to battle another gang!</Note> : null}
    {!d.you ? <RaisedButton testID="rf-gangwar-go" tone="wine" icon="gang" label="Open my gangs" onPress={() => setArenaTab("gang")} /> : null}
    <T size={10} color={arena.faint} style={styles.center}>Points = correct answers scored for your gang in Gang vs Gang battles.</T>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, list: { gap: 10 }, kicker: { letterSpacing: 1.5 },
  hero: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  last: { padding: 12, gap: 10 }, podium: { flexDirection: "row", justifyContent: "space-around", alignItems: "flex-end" }, podiumCell: { flex: 1, alignItems: "center", gap: 3 },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 60, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  rowYou: { borderColor: arena.gold, backgroundColor: arena.panelHi },
  medal: { width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
});

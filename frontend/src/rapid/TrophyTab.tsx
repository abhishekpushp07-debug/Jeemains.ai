import React, { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Icon, T, tap } from "@/src/components/ui";
import { BADGE_ICON, useGameProfile } from "@/src/components/game";
import { playSfx } from "@/src/sfx";
import { arena } from "@/src/theme";
import { Alive, GEM_ORDER, GameIcon, Gem } from "./Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle, Segment } from "./arena";
import { Jelly, Pop } from "./juice";
import { Bar, Face, GemStrip, NameLine, Note, crownText } from "./parts";
import { RushTrack } from "./RushTrack";
import { FriendsLeague, GangWarBoard } from "./Leagues";
import { ErrorBox } from "./ui";
import { go, ordinal, takeArenaPart } from "./social";

type Part = "ranks" | "rewards" | "matches";
const MEDAL = [arena.gold, "#D8DEE9", "#E0A36B"];
const day = (iso?: string) => (iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");

/** Ranks: everyone (All India), just your friends (weekly league), or the Gang War top 100. */
function Ranks({ uid }: { uid: string }) {
  const [board, setBoard] = useState<"all" | "friends" | "gangwar">("all");
  return <View style={styles.list}>
    <Segment prefix="rf-board-kind" value={board} onChange={setBoard} items={[["all", "All India"], ["friends", "Friends"], ["gangwar", "Gang War"]]} />
    {board === "all" ? <AllIndia uid={uid} /> : board === "friends" ? <FriendsLeague uid={uid} /> : <GangWarBoard uid={uid} />}
  </View>;
}

function AllIndia({ uid }: { uid: string }) {
  const router = useRouter();
  const board = useCached<any>(uid ? `u.${uid}.rfboard.JEE` : null, () => rf("/leaderboard?exam=JEE", uid), false);
  const reload = board.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const d = board.data;
  return <View testID="rf-leaderboard" style={styles.list}>
    <ErrorBox testID="rf-board-error" error={board.error} retry={board.reload} />
    {!d && board.loading ? <ActivityIndicator testID="rf-board-loading" color={arena.aqua} /> : null}
    {d?.you ? <Panel gold testID="rf-board-your-stats" style={styles.mine}>
      <GameIcon name="trophy" size={48} />
      <View style={styles.flex}>
        <T testID="rf-board-your-rank" w="heavy" size={18} color={arena.gold}>{d.you.rank ? `Your rank #${d.you.rank}` : "Your race starts here"}</T>
        <T testID="rf-board-your-xp" w="bold" size={12} color={arena.aqua}>{d.you.xp} XP · Level {d.you.level}</T>
      </View>
    </Panel> : null}
    {d?.items?.map((row: any, i: number) => <Pop key={row.rank} delay={Math.min(i, 8) * 40}>
      <Pressable testID={`rf-board-row-${row.rank}`} disabled={!row.pid} onPress={() => { tap(); router.push(go.player(row.pid)); }} accessibilityRole="button" accessibilityLabel={`Rank ${row.rank}, ${row.name}${crownText(row.crown)}`} style={[styles.row, row.you && styles.rowYou]}>
        <View style={[styles.medal, row.rank <= 3 && { backgroundColor: MEDAL[row.rank - 1], borderColor: arena.badgeInk }]}><T testID={`rf-board-rank-${row.rank}`} w="heavy" size={13} color={row.rank <= 3 ? arena.badgeInk : arena.muted}>{row.rank}</T></View>
        <Face p={row} size={40} />
        <View style={styles.flex}>
          <View testID={`rf-board-name-${row.rank}`}><NameLine name={`${row.name}${row.you ? " (you)" : ""}`} crown={row.crown} size={14} testID={`rf-board-crown-${row.rank}`} /></View>
          <T w="bold" size={11} color={arena.muted}>Level {row.level} · {row.wins} win{row.wins === 1 ? "" : "s"}</T>
        </View>
        <T testID={`rf-board-xp-${row.rank}`} w="heavy" size={13} color={arena.gold}>{row.xp} XP</T>
      </Pressable>
    </Pop>)}
    {d && !d.items.length ? <Note testID="rf-board-empty">Nobody on the board yet. Play a sprint and take the first spot!</Note> : null}
    <T testID="rf-board-wallet-note" size={10} color={arena.faint} style={styles.center}>Ranked by Rapid Fire practice XP. Not exam ranks.</T>
  </View>;
}

function Rewards({ uid }: { uid: string }) {
  const router = useRouter();
  const prof = useGameProfile(uid), p = prof.data;
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const claim = async (id: string) => {
    setBusy(id); setError("");
    try { await rf("/quests/claim", uid, { method: "POST", body: { id } }); playSfx("coin"); prof.reload(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  return <View style={styles.list}>
    <Panel testID="rf-streak-card" style={styles.streak}>
      <Alive kind="breathe"><GameIcon name="flame" size={64} /></Alive>
      <View style={styles.flex}>
        <T testID="game-hud-streak" w="heavy" size={22} color={arena.text}>{p?.streak ?? "—"} day streak</T>
        <T testID="rf-quests-reset" w="bold" size={12} color={arena.aqua}>Best {p?.best_streak ?? 0} · {p?.freezes ?? 0} streak freeze{p?.freezes === 1 ? "" : "s"}</T>
        <T size={11} color={arena.muted}>{p?.played_today ? "Done for today. See you tomorrow!" : "Play one match today to keep it burning."}</T>
      </View>
    </Panel>
    <RushTrack uid={uid} rush={p?.rush} onClaimed={prof.reload} />
    <SectionTitle title="Daily quests" />
    {(p?.quests || []).map((q: any) => <Panel flat key={q.id} testID={`rf-quest-${q.id}`} style={styles.quest}>
      <GameIcon name="chest" size={44} />
      <View style={styles.questCopy}>
        <T w="heavy" size={14} color={arena.text}>{q.title}</T>
        <Bar value={q.progress / q.goal} color={q.done ? arena.gold : arena.teal} />
        <T w="bold" size={11} color={arena.muted}>{q.progress}/{q.goal} · {q.coins} coins</T>
      </View>
      {q.done && !q.claimed ? <RaisedButton testID={`rf-quest-claim-${q.id}`} label="Claim" height={44} busy={busy === q.id} disabled={!!busy} onPress={() => claim(q.id)} style={styles.claim} />
        : <T testID={`rf-quest-state-${q.id}`} w="heavy" size={12} color={q.claimed ? arena.gold : arena.aqua}>{q.claimed ? "Claimed ✓" : "Going"}</T>}
    </Panel>)}
    <ErrorBox testID="rf-quest-claim-error" error={error || prof.error} retry={prof.reload} />
    <SectionTitle title="Diamond Vault" action="Open" testID="rf-rewards-open-vault" onAction={() => router.push("/rapid/vault" as any)} />
    <Jelly testID="rf-rewards-vault" accessibilityLabel="Diamond Vault" onPress={() => router.push("/rapid/vault" as any)}>
      <Panel gold style={styles.vault}><GemStrip diamonds={p?.diamonds} size={42} labels wings /><T w="bold" size={12} color={arena.aqua} style={styles.center}>Longest Phoenix streak: {p?.best_phoenix ?? 0}</T></Panel>
    </Jelly>
    <SectionTitle title="Trophies" />
    <View style={styles.trophies}>{(p?.badges || []).map((b) => <View key={b.id} testID={`rf-badge-${b.id}`} style={[styles.trophy, !b.earned && styles.locked]}>
      <View style={[styles.trophyIcon, b.earned && styles.trophyOn]}><Icon name={b.earned ? BADGE_ICON[b.id] : "lock"} size={26} color={b.earned ? arena.badgeInk : arena.faint} /></View>
      <T w="heavy" size={12} color={b.earned ? arena.gold : arena.muted} numberOfLines={1}>{b.title}</T>
      <T size={10} color={arena.muted} numberOfLines={2} style={styles.center}>{b.body}</T>
    </View>)}</View>
  </View>;
}

function Matches({ uid }: { uid: string }) {
  const router = useRouter();
  const [kind, setKind] = useState<"duels" | "solo">("duels");
  const duels = useCached<any>(uid ? `u.${uid}.rfduels.JEE` : null, () => rf("/duels?exam=JEE", uid), false);
  const solo = useCached<any>(uid ? `u.${uid}.rfhist.JEE` : null, () => rf("/history?exam=JEE", uid), false);
  const { reload: reloadDuels } = duels, { reload: reloadSolo } = solo;
  useFocusEffect(useCallback(() => { reloadDuels(); reloadSolo(); }, [reloadDuels, reloadSolo]));
  const q = kind === "duels" ? duels : solo;
  const gems = (won?: Record<string, number>) => GEM_ORDER.filter((c) => won?.[c]).map((c) => <View key={c} style={styles.gemChip}><Gem color={c} size={20} /><T w="heavy" size={11} color={arena.text}>{won![c]}</T></View>);
  return <View testID="rf-history" style={styles.list}>
    <Segment prefix="rf-history-tab" value={kind} onChange={setKind} items={[["duels", "Matches"], ["solo", "Solo sprints"]]} />
    <ErrorBox testID="rf-history-error" error={q.error} retry={q.reload} />
    {!q.data && q.loading ? <ActivityIndicator color={arena.aqua} /> : null}
    {kind === "duels" ? duels.data?.items?.map((m: any) => {
      const group = m.scores.length > 2, others = m.scores.filter((s: any) => !s.you), me = m.scores.find((s: any) => s.you);
      return <Pressable key={m.id} testID={`rf-match-${m.id}`} onPress={() => { tap(); router.push(go.duel({ review: m.id })); }} accessibilityRole="button" style={styles.row}>
        <View style={[styles.result, m.won && styles.resultWon]}><T w="heavy" size={12} color={m.won ? arena.badgeInk : arena.text}>{group ? ordinal(m.place) : m.won ? "WON" : m.tie ? "TIE" : "LOST"}</T></View>
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{group ? `${m.scores.length} players` : `vs ${others[0]?.name || "Rival"}`} · {me?.score ?? 0}{group ? "" : ` – ${others[0]?.score ?? 0}`}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{m.cup ? "Cup · " : m.team ? "Gang War · " : ""}{m.label || m.chapter || "Mixed"} · {day(m.finished_at)}</T>
        </View>
        <View style={styles.gemRow}>{gems(m.diamonds)}</View>
      </Pressable>;
    }) : solo.data?.items?.map((s: any) => <Pressable key={s.id} testID={`rf-solo-${s.id}`} onPress={() => { tap(); router.push({ pathname: "/rapid/session", params: { review: s.id } }); }} accessibilityRole="button" style={styles.row}>
      <View style={styles.result}><T w="heavy" size={13} color={arena.text}>{s.summary?.score ?? 0}/{s.summary?.total ?? 0}</T></View>
      <View style={styles.flex}>
        <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{s.mode === "weak_revision" ? "Weak cards" : "Solo Sprint"} · {s.chapter || "Mixed"}</T>
        <T w="bold" size={11} color={arena.muted}>{s.label || s.subject} · {day(s.completed_at)}</T>
      </View>
      <View style={styles.gemRow}>{gems(s.diamonds)}</View>
    </Pressable>)}
    {q.data && !q.data.items.length ? <Note testID="rf-history-empty">{kind === "duels" ? "No matches yet. Hit PLAY in the Arena!" : "No sprints yet. Try a Solo Sprint."}</Note> : null}
  </View>;
}

/** Trophy tab: Ranks (leaderboard), Rewards (streak, quests, Diamond Vault, trophies) and My matches (history). */
export function TrophyTab() {
  const uid = useAuth().user?.id || "";
  const [part, setPart] = useState<Part>(() => (takeArenaPart() as Part) || "ranks");
  return <View style={styles.flex} testID="arena-trophy">
    <View style={styles.head}>
      <GoldTitle size={24}>Trophy Room</GoldTitle>
      <Segment prefix="trophy-tab" value={part} onChange={setPart} items={[["ranks", "Ranks"], ["rewards", "Rewards"], ["matches", "My matches"]]} />
    </View>
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
      {part === "ranks" ? <Ranks uid={uid} /> : part === "rewards" ? <Rewards uid={uid} /> : <Matches uid={uid} />}
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, head: { paddingHorizontal: 16, gap: 8, paddingTop: 4 },
  content: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 28 }, list: { gap: 10 },
  mine: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 60, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  rowYou: { borderColor: arena.gold, backgroundColor: arena.panelHi },
  medal: { width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  streak: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  quest: { flexDirection: "row", alignItems: "center", gap: 10, padding: 12 }, questCopy: { flex: 1, minWidth: 0, gap: 5 }, claim: { width: 92 },
  vault: { padding: 14, gap: 10 },
  trophies: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  trophy: { width: "31.5%", minHeight: 118, alignItems: "center", gap: 3, padding: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim }, locked: { opacity: 0.6 },
  trophyIcon: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  trophyOn: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
  result: { minWidth: 52, height: 34, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  resultWon: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
  gemRow: { flexDirection: "row", gap: 4, flexShrink: 0 }, gemChip: { alignItems: "center" },
});

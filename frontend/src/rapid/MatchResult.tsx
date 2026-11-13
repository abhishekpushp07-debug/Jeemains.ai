import React, { useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { rf, uuid } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { RewardPanel } from "@/src/components/game";
import { arena, rapidColors as colors } from "@/src/theme";
import { GameIcon, PhoenixDiamond } from "./Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "./arena";
import { RapidDiagram } from "./Diagram";
import { Confetti, Jelly, Twinkles } from "./juice";
import { MatchPlayer, Podium, shownName } from "./MatchParts";
import { Note, PersonRow } from "./parts";
import { RapidText } from "./RapidText";
import { DiamondsWon } from "./StreakGem";
import { ErrorBox } from "./ui";
import { go, ordinal, sendChallenge, useFriends } from "./social";

const MISS: Record<string, string> = { timed_out: "Timed out", skipped: "Skipped" };

/** End of a match. 1 v 1: VICTORY with the Phoenix or GOOD FIGHT, score against score. 3 to 5 players: podium and full ranking. Then diamonds, rewards and what to do next. */
export function MatchResult({ d, uid, historical, onDone }: { d: any; uid: string; historical?: boolean; onDone: () => void }) {
  const router = useRouter();
  const friends = useFriends(uid);
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [review, setReview] = useState(false);
  const players: MatchPlayer[] = d.players;
  const me = players.find((p) => p.you), others = players.filter((p) => !p.you), opp = others[0];
  const group = players.length > 2, won = d.winner === d.you, tie = d.winner === "tie";
  const ranked = [...players].sort((a, b) => a.rank - b.rank);
  const humans = others.filter((p) => !p.bot && p.pid);
  const friendPids = new Set((friends.data?.items || []).map((f) => f.pid));
  const mine = me?.answers || [];
  const missed = (d.cards as any[]).map((c, k) => ({ c, k, a: mine[k] })).filter((x) => x.a?.outcome !== "correct");
  const open = (pid: string) => router.push(go.player(pid));

  const again = async () => {
    setBusy("again"); setError("");
    try {
      // Real rivals get a new Match Room with everyone invited; a practice rival is simply a fresh match.
      if (humans.length) router.replace(go.room(await sendChallenge(uid, { rematch_of: d.id, subject: d.subject, chapter: d.chapter })));
      else router.replace(go.duel({ mode: d.mode === "random" ? "random" : "ai", subject: d.subject, chapter: d.chapter || "", r: uuid() }));
    } catch (e: any) { setError(e.message); setBusy(""); }
  };
  const add = async (pid: string) => {
    setBusy(pid); setError("");
    try { await rf("/friends", uid, { method: "POST", body: { pid } }); invalidate(`u.${uid}.rffriends`); friends.reload(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };

  return <View style={styles.flex}>
    <ScrollView testID="duel-result" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
      <Panel gold={won} testID="duel-result-card" style={styles.hero}>
        {won ? <View>
          <PhoenixDiamond width={236} breathe burst={!historical} testID="duel-result-art" />
          <Twinkles spots={[[10, 16, 16], [90, 20, 13], [50, 2, 12], [22, 84, 10], [80, 80, 12]]} />
        </View> : <GameIcon name={tie ? "swords" : "flame"} size={88} testID="duel-result-art" />}
        <GoldTitle size={won ? 42 : 34} center testID="duel-outcome">{won ? "VICTORY" : tie ? "IT’S A TIE" : "GOOD FIGHT"}</GoldTitle>
        {group ? <T testID="duel-final-place" w="heavy" size={16} color={arena.aqua}>{ordinal(me?.rank || 1)} of {players.length} · {me?.score ?? 0} correct</T>
          : <View testID="duel-final-score" style={styles.versus}>
            <View style={styles.side}><Avatar icon={me?.avatar} frame={me?.frame} size={54} /><T w="heavy" size={12} color={arena.gold} numberOfLines={1}>You</T></View>
            <View style={styles.score}>
              <T testID="duel-final-mine" w="heavy" size={44} color={won ? arena.gold : arena.text}>{me?.score ?? 0}</T>
              <T w="heavy" size={26} color={arena.faint}>–</T>
              <T testID="duel-final-theirs" w="heavy" size={44} color={arena.text}>{opp?.score ?? 0}</T>
            </View>
            <View style={styles.side}><Avatar icon={opp?.avatar} frame={opp?.frame} size={54} /><T w="heavy" size={12} color={arena.text} numberOfLines={1}>{shownName(opp)}</T></View>
          </View>}
        {d.tie_break ? <T testID="duel-tie-break" size={12} color={arena.muted} style={styles.center}>Equal score. The faster player takes it.</T> : null}
        {opp?.forfeit && !group ? <T size={12} color={arena.muted} style={styles.center}>{shownName(opp)} left the match.</T> : null}
        {d.finished_at ? <T testID="duel-finished-at" size={11} color={arena.faint}>{new Date(d.finished_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}</T> : null}
      </Panel>

      {group ? <>
        <Podium players={players} onOpen={open} />
        <View style={styles.list} testID="duel-ranking">
          {ranked.map((p) => <View key={p.pid || p.rank} testID={`duel-rank-${p.rank}`} style={[styles.rank, p.you && styles.rankYou]}>
            <T w="heavy" size={15} color={arena.gold} style={styles.place}>{ordinal(p.rank)}</T>
            <Avatar icon={p.avatar} frame={p.frame} size={38} />
            <T w="heavy" size={14} color={p.you ? arena.gold : arena.text} numberOfLines={1} style={styles.flex}>{shownName(p)}{p.forfeit ? " · left" : ""}</T>
            <T w="heavy" size={18} color={arena.text}>{p.score}</T>
          </View>)}
        </View>
      </> : null}

      <DiamondsWon reward={d.reward} testID="duel-diamonds" />
      <RewardPanel reward={d.reward} testID="duel-reward" historical={historical} title={historical ? "Match rewards" : won ? "A well-earned victory" : tie ? "What a close match!" : "Every round makes you sharper"} />

      {others.length ? <SectionTitle title={group ? "Players" : "Your rival"} /> : null}
      {others.map((p, i) => p.bot || !p.pid
        ? <PersonRow key={i} testID="duel-rival-practice" p={{ name: p.name, avatar: p.avatar, frame: p.frame }} sub="Practice rival" />
        : <PersonRow key={p.pid} testID={`duel-player-${p.pid}`} p={{ name: p.name, avatar: p.avatar, frame: p.frame }} sub={`Level ${p.level ?? 1} · ${p.wins ?? 0} win${p.wins === 1 ? "" : "s"} · View profile`} onPress={() => open(p.pid!)}
          right={friendPids.has(p.pid) ? <T testID={`duel-friend-${p.pid}`} w="heavy" size={12} color={arena.gold}>Friends ✓</T>
            : <RaisedButton testID={`duel-add-friend-${p.pid}`} label="Add Friend" height={42} busy={busy === p.pid} disabled={!!busy || !friends.data} onPress={() => add(p.pid!)} style={styles.add} />} />)}

      <Jelly testID="duel-toggle-misses" accessibilityLabel={review ? "Hide the cards you missed" : `Review ${missed.length} missed cards`} disabled={!missed.length} onPress={() => setReview(!review)} style={styles.reviewToggle}>
        <GameIcon name="target" size={34} />
        <T w="heavy" size={14} color={arena.text} style={styles.flex}>{!missed.length ? "No missed cards. Flawless!" : review ? "Hide missed cards" : `Review ${missed.length} missed card${missed.length === 1 ? "" : "s"}`}</T>
      </Jelly>
      {review ? missed.map(({ c, k, a }) => <View key={c.id} testID={`duel-review-${k}`} style={styles.reviewCard}>
        <T w="bold" size={11} color={arena.muted}>Card {k + 1} · {c.chapter}</T>
        <RapidText text={c.prompt} size={15} testID={`duel-review-prompt-${k}`} />
        <RapidDiagram diagram={c.diagram} testID={`duel-review-diagram-${k}`} />
        {c.formula ? <RapidText text={c.formula} size={17} testID={`duel-review-formula-${k}`} /> : null}
        <T size={12} color={colors.error}>{!a ? "Not reached" : a.outcome === "incorrect" ? `You chose: ${c.options[a.choice ?? 0]}` : MISS[a.outcome] || "Missed"}</T>
        <T size={12} w="bold" color={colors.success}>Correct: {c.options[c.answer]}</T>
        {c.explain ? <T size={11} color={arena.muted}>{c.explain}</T> : null}
      </View>) : null}
      <Note testID="duel-practice-note">Practice match. It never changes exam marks, ranks or your series streak.</Note>
    </ScrollView>

    <View style={styles.dock}>
      <ErrorBox testID="duel-result-error" error={error} />
      <View style={styles.row}>
        <RaisedButton testID="duel-done" tone="wine" label="Done" height={58} disabled={busy === "again"} onPress={onDone} style={styles.flex} />
        <RaisedButton testID="duel-rematch" icon="swords" height={58} streak label={humans.length ? "REMATCH" : "PLAY AGAIN"} busy={busy === "again"} disabled={!!busy} onPress={again} style={styles.wide} />
      </View>
    </View>
    {won && !historical ? <Confetti count={36} /> : null}
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, wide: { flex: 1.7 }, center: { textAlign: "center" }, row: { flexDirection: "row", gap: 10 }, list: { gap: 8 },
  content: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 14 },
  hero: { alignItems: "center", gap: 6, paddingVertical: 18, paddingHorizontal: 14 },
  versus: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", alignSelf: "stretch", gap: 6 }, side: { width: 78, alignItems: "center", gap: 4 },
  score: { flexDirection: "row", alignItems: "center", gap: 10 },
  rank: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 56, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  rankYou: { borderColor: arena.gold, backgroundColor: arena.panelHi }, place: { width: 38 }, add: { width: 116 },
  reviewToggle: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 56, paddingHorizontal: 12, borderRadius: 18, backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 5, borderBottomColor: arena.panelEdge },
  reviewCard: { gap: 6, padding: 14, borderRadius: 18, backgroundColor: colors.custom_reading, borderWidth: 1.5, borderColor: arena.rim },
  dock: { paddingHorizontal: 16, paddingTop: 8, gap: 8 },
});

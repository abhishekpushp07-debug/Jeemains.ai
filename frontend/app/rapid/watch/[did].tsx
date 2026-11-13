import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, BackHandler, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { ZoomIn, useReducedMotion } from "react-native-reanimated";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { Icon, T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { Emblem, GameIcon } from "@/src/rapid/Art";
import { ArenaBg, CloseButton, GoldTitle, Panel, RaisedButton } from "@/src/rapid/arena";
import { LiveDot, Pop } from "@/src/rapid/juice";
import { RivalGem } from "@/src/rapid/StreakGem";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { go, ordinal } from "@/src/rapid/social";

type P = { name: string; avatar?: string | null; frame?: string | null; pid?: string | null; bot: boolean; level: number; score: number; answered: number; rank: number; team?: "a" | "b" | null;
  done: boolean; forfeit: boolean; streak: number; won: boolean; trail: boolean[] };

/** The last answers as dots: green right, red wrong. Spectators never see the questions themselves. */
function Trail({ trail }: { trail: boolean[] }) {
  return <View style={styles.trail}>{trail.map((ok, i) => <View key={i} style={[styles.pip, { backgroundColor: ok ? arena.online : arena.danger }]} />)}</View>;
}

function Bar({ p, total, gold }: { p: P; total: number; gold?: boolean }) {
  return <View style={styles.track}><View style={[styles.fill, { width: `${Math.min(1, p.answered / total) * 100}%`, backgroundColor: gold ? arena.gold : arena.tealHi }]} /></View>;
}

/** A big side of a 1 v 1: portrait, name, live score, progress, Phoenix streak and the last answers. */
function Fighter({ p, total, testID }: { p: P; total: number; testID: string }) {
  const reduced = useReducedMotion();
  return <View testID={testID} style={[styles.fighter, p.won && styles.fighterWon, p.forfeit && styles.gone]}>
    <Avatar icon={p.avatar} frame={p.frame} size={76} />
    <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{p.name}</T>
    <T w="bold" size={10} color={arena.aqua}>{p.bot ? "Practice rival" : `Level ${p.level}`}</T>
    <Animated.View key={p.score} entering={reduced ? undefined : ZoomIn.duration(220)}><T testID={`${testID}-score`} w="heavy" size={48} color={p.won ? arena.gold : arena.text}>{p.score}</T></Animated.View>
    <RivalGem streak={p.streak || 0} size={24} testID={`${testID}-streak`} />
    <Bar p={p} total={total} gold={p.won} />
    <T w="bold" size={10} color={arena.muted}>{p.forfeit ? "Left the match" : p.done ? "Finished" : `${p.answered}/${total} cards`}</T>
    <Trail trail={p.trail} />
  </View>;
}

/** Watching a live match: scores, streaks and progress as they happen. 1 v 1, 3 to 5 players, or gang against gang. */
function Watch() {
  const { did } = useLocalSearchParams<{ did: string }>();
  const router = useRouter(), insets = useSafeAreaInsets(), uid = useAuth().user?.id || "";
  const [d, setD] = useState<any>(null), [error, setError] = useState("");
  const [, tick] = useState(0);
  const anchor = useRef({ server: 0, local: 0 });
  const load = useCallback(async () => {
    try { const v = await rf(`/duels/${did}/watch`, uid); anchor.current = { server: v.server_now, local: Date.now() / 1000 }; setD(v); setError(""); }
    catch (e: any) { setError(e.message); }
  }, [did, uid]);
  const over = d?.status === "finished";
  useEffect(() => {
    if (!uid || over) return;
    load();
    const poll = setInterval(load, 1500), second = setInterval(() => tick((n) => n + 1), 1000);
    return () => { clearInterval(poll); clearInterval(second); };
  }, [uid, over, load]);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"));
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { back(); return true; });
    return () => sub.remove();
  }, [])); // eslint-disable-line react-hooks/exhaustive-deps

  const now = anchor.current.server + (Date.now() / 1000 - anchor.current.local);
  const startsIn = d ? Math.max(0, Math.ceil(d.start_at - now)) : 0;
  const players: P[] = d?.players || [];
  const ranked = [...players].sort((a, b) => a.rank - b.rank);
  const winner = players.find((p) => p.won);

  let body: React.ReactNode;
  if (!d) body = <View style={styles.middle}>{error ? <><ErrorBox testID="watch-error" error={error} retry={load} /><RaisedButton testID="watch-back" tone="wine" label="Back" onPress={back} style={styles.stretch} /></> : <ActivityIndicator testID="watch-loading" color={arena.aqua} size="large" />}</View>;
  else body = <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <Panel gold={over} testID="watch-status" style={styles.status}>
      {over ? <GameIcon name="trophy" size={44} /> : <LiveDot size={12} />}
      <View style={styles.flex}>
        <T testID="watch-status-text" w="heavy" size={16} color={over ? arena.gold : arena.text}>{over ? (d.team_mode ? (d.winner_team ? `${d.teams[d.winner_team].name} win the war!` : "The gangs are level") : d.tie ? "It’s a tie!" : `${winner?.name || "Winner"} wins!`) : startsIn ? `Starts in ${startsIn}s` : "LIVE NOW"}</T>
        <T w="bold" size={11} color={arena.aqua} numberOfLines={1}>{d.label} · {d.total} cards</T>
      </View>
      <View testID="watch-viewers" style={styles.viewers}><Icon name="eye" size={14} color={arena.aqua} /><T w="heavy" size={12} color={arena.aqua}>{d.watchers || 1}</T></View>
    </Panel>

    {d.team_mode && d.teams ? <View style={styles.teams} testID="watch-teams">
      {(["a", "b"] as const).map((t) => <View key={t} style={[styles.team, d.winner_team === t && styles.fighterWon]}>
        <Emblem id={d.teams[t].emblem} size={54} />
        <T w="heavy" size={13} color={arena.text} numberOfLines={1}>{d.teams[t].name}</T>
        <T testID={`watch-team-${t}`} w="heavy" size={40} color={d.winner_team === t ? arena.gold : arena.text}>{d.teams[t].score}</T>
        <T w="bold" size={10} color={arena.muted}>best {d.teams[t].counted} of {d.teams[t].players} count</T>
        {players.filter((p) => p.team === t).map((p, i) => <View key={i} style={styles.mini}><Avatar icon={p.avatar} frame={p.frame} size={24} /><T w="bold" size={11} color={arena.text} numberOfLines={1} style={styles.flex}>{p.name}</T><T w="heavy" size={12} color={arena.gold}>{p.score}</T></View>)}
      </View>)}
    </View> : players.length === 2 ? <View style={styles.duo} testID="watch-duo">
      <Fighter p={players[0]} total={d.total} testID="watch-p0" />
      <View style={styles.vs}><T w="heavy" size={13} color={arena.badgeInk}>VS</T></View>
      <Fighter p={players[1]} total={d.total} testID="watch-p1" />
    </View> : <View style={styles.list} testID="watch-group">
      {ranked.map((p, i) => <Pop key={p.pid || i} delay={i * 60}><View testID={`watch-rank-${p.rank}`} style={[styles.rankRow, p.rank === 1 && styles.fighterWon, p.forfeit && styles.gone]}>
        <T w="heavy" size={15} color={arena.gold} style={styles.place}>{ordinal(p.rank)}</T>
        <Avatar icon={p.avatar} frame={p.frame} size={40} />
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{p.name}</T>
          <Bar p={p} total={d.total} gold={p.rank === 1} />
          <Trail trail={p.trail} />
        </View>
        <RivalGem streak={p.streak || 0} size={20} testID={`watch-rank-${p.rank}-streak`} />
        <T w="heavy" size={24} color={arena.text}>{p.score}</T>
      </View></Pop>)}
    </View>}

    <T testID="watch-note" size={11} color={arena.faint} style={styles.center}>You are watching. Questions stay hidden so nobody can help from outside.</T>
  </ScrollView>;

  return <ArenaBg testID="watch-screen">
    <View style={[styles.frame, { paddingTop: insets.top + 6, paddingBottom: insets.bottom + 10 }]}>
      <View style={styles.top}>
        <CloseButton testID="watch-close" label="Stop watching" onPress={back} />
        <View style={styles.flex}>
          <GoldTitle testID="watch-title">{d?.cup_id ? "Cup match" : d?.team_mode ? "Gang War" : "Live match"}</GoldTitle>
          <T w="bold" size={12} color={arena.aqua} numberOfLines={1}>Spectator mode</T>
        </View>
        <Icon name="eye" size={30} color={arena.gold} />
      </View>
      {body}
      {d?.cup_id ? <View style={styles.dock}><RaisedButton testID="watch-cup" icon="trophy" tone="wine" label="Back to the bracket" onPress={() => router.replace(go.cup(d.cup_id))} /></View> : null}
    </View>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, stretch: { alignSelf: "stretch" }, center: { textAlign: "center" }, list: { gap: 8 }, place: { width: 38 },
  frame: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" },
  top: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, minHeight: 56 },
  middle: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 20 },
  content: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 12 },
  status: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14 },
  viewers: { flexDirection: "row", alignItems: "center", gap: 4, height: 30, paddingHorizontal: 10, borderRadius: 15, backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.rim },
  duo: { flexDirection: "row", alignItems: "center", gap: 6 },
  fighter: { flex: 1, minWidth: 0, alignItems: "center", gap: 4, paddingVertical: 14, paddingHorizontal: 8, borderRadius: 22, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  fighterWon: { borderColor: arena.gold, backgroundColor: arena.panelHi }, gone: { opacity: 0.5 },
  vs: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 2, borderColor: arena.goldDeep },
  track: { height: 8, alignSelf: "stretch", borderRadius: 4, backgroundColor: arena.panelEdge, overflow: "hidden", marginTop: 2 }, fill: { height: "100%", borderRadius: 4 },
  trail: { flexDirection: "row", gap: 3, minHeight: 8, marginTop: 2 }, pip: { width: 8, height: 8, borderRadius: 4 },
  teams: { flexDirection: "row", gap: 8 },
  team: { flex: 1, minWidth: 0, alignItems: "center", gap: 4, padding: 10, borderRadius: 22, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  mini: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "stretch" },
  rankRow: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  dock: { paddingHorizontal: 16, paddingTop: 8 },
});

export default withRapid(Watch, { banner: false });

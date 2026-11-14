import React from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "./arena";
import { Pop } from "./juice";
import { Crown, Note } from "./parts";
import { day, go } from "./social";

type Win = { id: string; label: string; size: number; kind: "open" | "private"; humans: number; finished_at: string };
export type Cups = { won: number; real: number; played: number; recent: Win[] };

function Stat({ label, value, testID }: { label: string; value: string | number; testID: string }) {
  return <View testID={testID} style={styles.stat}><T w="heavy" size={22} color={arena.gold}>{value}</T><T w="bold" size={10} color={arena.muted} style={styles.center}>{label}</T></View>;
}

/** One cup lifted: what it was played on, how big it was, and whether real players were beaten. */
function WinRow({ w, i }: { w: Win; i: number }) {
  const rivals = w.humans - 1;
  return <Pop delay={i * 60}>
    <View testID={`player-cup-win-${w.id}`} style={styles.win}>
      <GameIcon name="trophy" size={34} />
      <View style={styles.flex}>
        <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{w.label}</T>
        <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{day(w.finished_at)} · {w.size} players · {w.kind === "open" ? "Open" : "Friends"}</T>
      </View>
      <View style={[styles.tag, rivals > 0 ? styles.tagReal : styles.tagPractice]}>
        <T w="heavy" size={10} color={rivals > 0 ? arena.badgeInk : arena.muted}>{rivals > 0 ? `BEAT ${rivals} REAL` : "PRACTICE"}</T>
      </View>
    </View>
  </Pop>;
}

/**
 * Cup Champion showcase on a profile: every Knockout Cup won (wins against real players counted apart), cups played,
 * and the last five titles. Your own profile gets a button to go and win (or defend) the crown.
 */
export function CupShowcase({ cups, name, me, onCheer }: { cups: Cups; name: string; me: boolean; onCheer?: () => void }) {
  const router = useRouter();
  const champ = cups.won > 0, rate = cups.played ? Math.min(100, Math.round((cups.won / cups.played) * 100)) : 0;
  return <>
    <SectionTitle title="Trophy Cabinet" />
    <Panel gold testID="player-cups" style={styles.panel}>
      <LinearGradient pointerEvents="none" colors={[arena.goldSoft, arena.clear]} style={StyleSheet.absoluteFill} />
      <View style={styles.head}>
        <Alive kind={champ ? "breathe" : "float"}><GameIcon name="trophy" size={champ ? 88 : 64} /></Alive>
        <View style={styles.flex}>
          <T w="heavy" size={11} color={arena.aqua} style={styles.kicker}>KNOCKOUT CUPS</T>
          {champ ? <>
            <View style={styles.titleRow}>
              <GoldTitle size={26} testID="player-cups-titles">{cups.won} {cups.won === 1 ? "title" : "titles"}</GoldTitle>
              <Crown c={cups} size="lg" testID="player-cups-crown" />
            </View>
            <T testID="player-cups-line" w="bold" size={12} color={arena.text}>{cups.real ? `${cups.real} won against real players` : "Won against practice rivals so far"}</T>
          </> : <>
            <GoldTitle size={22} testID="player-cups-titles">No crown yet</GoldTitle>
            <T testID="player-cups-line" w="bold" size={12} color={arena.muted}>{me ? "Win a Knockout Cup and the crown sits next to your name everywhere." : `${name} has not won a cup yet.`}</T>
          </>}
        </View>
      </View>
      <View style={styles.stats}>
        <Stat testID="player-cups-won" label="CUPS WON" value={cups.won} />
        <Stat testID="player-cups-real" label="VS REAL PLAYERS" value={cups.real} />
        <Stat testID="player-cups-played" label="CUPS PLAYED" value={cups.played} />
        <Stat testID="player-cups-rate" label="WIN %" value={cups.played ? `${rate}%` : "—"} />
      </View>
      {cups.recent.length ? <View style={styles.list}>
        <T w="heavy" size={11} color={arena.gold} style={styles.kicker}>LATEST TITLES</T>
        {cups.recent.map((w, i) => <WinRow key={w.id} w={w} i={i} />)}
      </View> : null}
      {champ && onCheer ? <RaisedButton testID="player-cups-cheer" tone="wine" glyph="party-popper" height={56} label="Cheer squad" sub={me ? "Watch them dance for your crown" : `Cheer for ${name}`} onPress={onCheer} /> : null}
      {me ? <RaisedButton testID="player-cups-play" icon="trophy" height={58} streak label={champ ? "DEFEND YOUR CROWN" : "PLAY A KNOCKOUT CUP"} sub="4 · 8 · 16 players" onPress={() => router.push(go.cups())} /> : null}
      <View style={styles.legend}>
        <Crown c={{ won: 1, real: 1 }} /><T w="bold" size={11} color={arena.muted}>beat real players</T>
        <Crown c={{ won: 1, real: 0 }} /><T w="bold" size={11} color={arena.muted}>practice cups</T>
      </View>
    </Panel>
    {!champ && !me ? <Note testID="player-cups-empty">Challenge {name} in a Friends Cup and see who takes the crown.</Note> : null}
  </>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, kicker: { letterSpacing: 1.5 },
  panel: { padding: 14, gap: 12, overflow: "hidden" },
  head: { flexDirection: "row", alignItems: "center", gap: 12 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" },
  stats: { flexDirection: "row", gap: 6 },
  stat: { flex: 1, minHeight: 64, alignItems: "center", justifyContent: "center", gap: 2, paddingHorizontal: 4, paddingVertical: 6, borderRadius: 14, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  list: { gap: 8 },
  win: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 56, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.goldDeep },
  tag: { paddingHorizontal: 8, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center", borderWidth: 1.5 },
  tagReal: { backgroundColor: arena.gold, borderColor: arena.goldDeep }, tagPractice: { backgroundColor: arena.panelEdge, borderColor: arena.rim },
  legend: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, flexWrap: "wrap" },
});

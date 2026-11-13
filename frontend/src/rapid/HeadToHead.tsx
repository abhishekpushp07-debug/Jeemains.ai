import React, { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Icon, T, tap } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GoldTitle, Panel } from "./arena";
import { Jelly } from "./juice";
import { ErrorBox, Sheet } from "./ui";
import { day, go, shortSubject } from "./social";

type Row = { id: string; subject: string; chapter?: string | null; you: number; them: number; won: boolean; tie: boolean; finished_at: string };
const verdict = (m: Row) => (m.won ? "WON" : m.tie ? "TIE" : "LOST");

/** Every 1 v 1 match against one player, newest first. Tapping a match opens its review. */
function History({ uid, pid, onOpen }: { uid: string; pid: string; onOpen: (id: string) => void }) {
  const q = useCached<{ items: Row[] }>(`u.${uid}.rfh2h.${pid}`, () => rf(`/players/${pid}/h2h`, uid), false);
  const rows = q.data?.items;
  if (!rows) return q.error ? <ErrorBox testID="h2h-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="h2h-loading" color={arena.aqua} />;
  return <>
    <View testID="h2h-form" style={styles.form}>
      <T w="bold" size={11} color={arena.muted}>Recent form</T>
      {rows.slice(0, 8).map((m) => <View key={m.id} style={[styles.dot, m.won && styles.won]}>
        <T w="heavy" size={11} color={m.won ? arena.badgeInk : m.tie ? arena.aqua : arena.danger}>{verdict(m)[0]}</T>
      </View>)}
    </View>
    {rows.map((m) => <Pressable key={m.id} testID={`h2h-row-${m.id}`} onPress={() => { tap(); onOpen(m.id); }} accessibilityRole="button" accessibilityLabel={`${verdict(m)} ${m.you} to ${m.them}. Open match review`} style={styles.row}>
      <View style={[styles.result, m.won && styles.won]}><T w="heavy" size={11} color={m.won ? arena.badgeInk : arena.text}>{verdict(m)}</T></View>
      <View style={styles.flex}>
        <T w="heavy" size={16} color={arena.text}>{m.you} – {m.them}</T>
        <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{shortSubject(m.subject)} · {m.chapter || "Mixed"} · {day(m.finished_at)}</T>
      </View>
      <Icon name="chevron-right" size={22} color={arena.aqua} />
    </Pressable>)}
    <T testID="h2h-note" size={11} color={arena.faint} style={styles.center}>1 v 1 matches only · newest first · last 30</T>
  </>;
}

/** Head-to-head on a player's profile: the running score, and one tap to see every match the two of you played. */
export function HeadToHeadCard({ uid, pid, name, h2h }: { uid: string; pid: string; name: string; h2h: { you: number; them: number; played: number } }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const card = <Panel flat testID="player-h2h" style={styles.card}>
    <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>HEAD TO HEAD</T>
    <T testID="player-h2h-score" w="heavy" size={22} color={arena.text} numberOfLines={2} style={styles.center}>You {h2h.you} – {h2h.them} {name}</T>
    <T size={11} color={arena.muted}>{h2h.played ? `${h2h.played} match${h2h.played === 1 ? "" : "es"} played, 1 v 1 only` : "No 1 v 1 match yet"}</T>
    {h2h.played ? <T testID="player-h2h-more" w="heavy" size={12} color={arena.gold}>See every match ›</T> : null}
  </Panel>;
  if (!h2h.played) return card;
  return <>
    <Jelly testID="player-h2h-open" accessibilityLabel={`Head to head with ${name}. See every match`} onPress={() => setOpen(true)}>{card}</Jelly>
    <Sheet visible={open} onClose={() => setOpen(false)} testID="h2h-sheet">
      <GoldTitle size={20} testID="h2h-title">You vs {name}</GoldTitle>
      {open ? <History uid={uid} pid={pid} onOpen={(id) => { setOpen(false); router.push(go.duel({ review: id })); }} /> : null}
    </Sheet>
  </>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 },
  card: { alignItems: "center", gap: 2, padding: 12 },
  form: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  dot: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  result: { minWidth: 50, height: 30, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  won: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});

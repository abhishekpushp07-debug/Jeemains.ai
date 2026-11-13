import React, { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Icon, T, tap } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { GoldTitle, Panel, RaisedButton } from "./arena";
import { Jelly } from "./juice";
import { ErrorBox, Sheet } from "./ui";
import { ScopeSheet } from "./ScopeSheet";
import { Pick, getScope } from "./scope";
import { day, go, sendChallenge } from "./social";

type Row = { id: string; subject: string; chapter?: string | null; label?: string; picks?: Pick[]; you: number; them: number; won: boolean; tie: boolean; finished_at: string };
const verdict = (m: Row) => (m.won ? "WON" : m.tie ? "TIE" : "LOST");
const lost = (m: Row) => !m.won && !m.tie;

/**
 * "Badla lo": you lost a 1 v 1 and want it back. First choose the battleground again (the lost match's subjects and
 * chapters are ready to keep or change), then the challenge goes to the same opponent. Render `sheet` next to the button.
 */
export function useBadla(uid: string, opts: { replace?: boolean } = {}) {
  const router = useRouter();
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const [ask, setAsk] = useState<{ id: string; picks: Pick[]; name?: string; before?: () => void } | null>(null);
  const send = async (picks: Pick[]) => {
    if (!ask) return;
    const { id, before } = ask;
    setBusy(id); setError("");
    try {
      const room = await sendChallenge(uid, { rematch_of: id, picks });
      before?.();
      if (opts.replace) router.replace(go.room(room)); else router.push(go.room(room));
    } catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const badla = (id: string, picks?: Pick[] | null, name?: string, before?: () => void) => { tap(); setError(""); setAsk({ id, picks: picks?.length ? picks : getScope(), name, before }); };
  const sheet = <ScopeSheet testID="rf-badla-sheet" visible={!!ask} onClose={() => setAsk(null)} subjects={cat.data?.subjects || []} value={ask?.picks || []} onDone={send}
    title="Badla lo! 🔥" hint={`Pick the battleground${ask?.name ? `, then ${ask.name} gets your challenge` : ""}`} action="SEND BADLA" />;
  return { badla, busy, error, sheet };
}

/** Every 1 v 1 match against one player, newest first. Tapping a match opens its review; a lost one has its own Badla button. */
function History({ uid, pid, name, onOpen, onSent }: { uid: string; pid: string; name: string; onOpen: (id: string) => void; onSent: () => void }) {
  const q = useCached<{ items: Row[] }>(`u.${uid}.rfh2h.${pid}`, () => rf(`/players/${pid}/h2h`, uid), false);
  const { badla, busy, error, sheet } = useBadla(uid);
  const rows = q.data?.items;
  if (!rows) return q.error ? <ErrorBox testID="h2h-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="h2h-loading" color={arena.aqua} />;
  const last = lost(rows[0] || ({ won: true } as Row)) ? rows[0] : null; // the top button only while the latest match is the one to take back
  return <>
    {last ? <RaisedButton testID="h2h-badla-top" icon="flame" height={62} streak label="BADLA LO" sub={`Rematch ${name} · choose the battleground`} busy={busy === last.id} disabled={!!busy} onPress={() => badla(last.id, last.picks, name, onSent)} /> : null}
    <ErrorBox testID="h2h-badla-error" error={error} />
    {sheet}
    <View testID="h2h-form" style={styles.form}>
      <T w="bold" size={11} color={arena.muted}>Recent form</T>
      {rows.slice(0, 8).map((m) => <View key={m.id} style={[styles.dot, m.won && styles.won]}>
        <T w="heavy" size={11} color={m.won ? arena.badgeInk : m.tie ? arena.aqua : arena.danger}>{verdict(m)[0]}</T>
      </View>)}
    </View>
    {rows.map((m) => <View key={m.id} style={styles.row}>
      <Pressable testID={`h2h-row-${m.id}`} onPress={() => { tap(); onOpen(m.id); }} accessibilityRole="button" accessibilityLabel={`${verdict(m)} ${m.you} to ${m.them}. Open match review`} style={styles.rowMain}>
        <View style={[styles.result, m.won && styles.won]}><T w="heavy" size={11} color={m.won ? arena.badgeInk : arena.text}>{verdict(m)}</T></View>
        <View style={styles.flex}>
          <T w="heavy" size={16} color={arena.text}>{m.you} – {m.them}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{day(m.finished_at)} · {m.label || m.chapter || "Mixed"}</T>
        </View>
      </Pressable>
      {lost(m) ? <RaisedButton testID={`h2h-badla-${m.id}`} tone="teal" label="Badla lo" height={44} busy={busy === m.id} disabled={!!busy} onPress={() => badla(m.id, m.picks, name, onSent)} style={styles.badla} />
        : <Icon name="chevron-right" size={22} color={arena.aqua} />}
    </View>)}
    <T testID="h2h-note" size={11} color={arena.faint} style={styles.center}>1 v 1 matches only · newest first · last 30</T>
  </>;
}

/** Head-to-head on a player's profile: the running score, and one tap to see every match the two of you played. */
export function HeadToHeadCard({ uid, pid, name, h2h }: { uid: string; pid: string; name: string; h2h: { you: number; them: number; played: number; last?: { id: string; won: boolean; tie: boolean; picks?: Pick[] } | null } }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const { badla, busy, error, sheet } = useBadla(uid);
  const owed = h2h.last && !h2h.last.won && !h2h.last.tie;
  const card = <Panel flat testID="player-h2h" style={styles.card}>
    <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>HEAD TO HEAD</T>
    <T testID="player-h2h-score" w="heavy" size={22} color={arena.text} numberOfLines={2} style={styles.center}>You {h2h.you} – {h2h.them} {name}</T>
    <T size={11} color={arena.muted}>{h2h.played ? `${h2h.played} match${h2h.played === 1 ? "" : "es"} played, 1 v 1 only` : "No 1 v 1 match yet"}</T>
    {h2h.played ? <T testID="player-h2h-more" w="heavy" size={12} color={arena.gold}>See every match ›</T> : null}
  </Panel>;
  if (!h2h.played) return card;
  return <>
    <Jelly testID="player-h2h-open" accessibilityLabel={`Head to head with ${name}. See every match`} onPress={() => setOpen(true)}>{card}</Jelly>
    {owed ? <RaisedButton testID="player-badla" icon="flame" height={56} streak label="BADLA LO" sub={`${name} won the last one. Take it back!`} busy={busy === h2h.last!.id} disabled={!!busy} onPress={() => badla(h2h.last!.id, h2h.last!.picks, name)} /> : null}
    <ErrorBox testID="player-badla-error" error={error} />
    {sheet}
    <Sheet visible={open} onClose={() => setOpen(false)} testID="h2h-sheet">
      <GoldTitle size={20} testID="h2h-title">You vs {name}</GoldTitle>
      {open ? <History uid={uid} pid={pid} name={name} onSent={() => setOpen(false)} onOpen={(id) => { setOpen(false); router.push(go.duel({ review: id })); }} /> : null}
    </Sheet>
  </>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 },
  card: { alignItems: "center", gap: 2, padding: 12 },
  form: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },
  dot: { width: 26, height: 26, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  rowMain: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 10, minHeight: 44 }, badla: { width: 104 },
  result: { minWidth: 50, height: 30, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  won: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});

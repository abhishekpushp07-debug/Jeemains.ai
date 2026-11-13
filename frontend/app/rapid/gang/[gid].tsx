import React, { useCallback, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate, useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Emblem } from "@/src/rapid/Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "@/src/rapid/arena";
import { InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, Sheet, withRapid } from "@/src/rapid/ui";
import { go, seenText, shortSubject, useFriends } from "@/src/rapid/social";

const day = (iso?: string) => (iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");

/** A gang's own screen: who is in it, one button to challenge everybody, its last matches, and the leader's controls. */
function Gang() {
  const { gid } = useLocalSearchParams<{ gid: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const q = useCached<any>(uid && gid ? `u.${uid}.rfgang.${gid}` : null, () => rf(`/gangs/${gid}`, uid), false);
  const friends = useFriends(uid);
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [note, setNote] = useState("");
  const [sheet, setSheet] = useState<"" | "add" | "more">("");
  const reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const g = q.data;
  const inside = new Set((g?.members || []).map((m: any) => m.pid));
  const addable = (friends.data?.items || []).filter((f) => !inside.has(f.pid));

  const act = async (key: string, run: () => Promise<any>, leaveAfter = false) => {
    setBusy(key); setError(""); setNote("");
    try {
      await run(); invalidate(`u.${uid}.rfgangs`);
      if (leaveAfter) { setSheet(""); router.back(); } else q.reload();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const add = (pid: string, name: string) => act("add" + pid, async () => {
    const r = await rf<any>(`/gangs/${gid}/members`, uid, { method: "POST", body: { pids: [pid] } });
    setNote(r.added ? `${name} joined the gang.` : r.skipped[0] || "Already a member.");
  });

  return <InnerScreen testID="gang-screen" title={g?.name || "Gang"} sub={g ? `${g.members.length}/${g.max} members · ${g.online} online` : undefined}
    footer={g ? <RaisedButton testID="gang-challenge" icon="swords" height={62} streak label="CHALLENGE GANG" sub={g.members.length < 2 ? "Add a member first" : "Up to 5 players per match"} disabled={g.members.length < 2} onPress={() => router.push(go.challenge({ gang: gid }))} /> : undefined}>
    {!g ? (q.error ? <ErrorBox testID="gang-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="gang-loading" color={arena.aqua} size="large" />) : <>
      <Panel gold testID="gang-card" style={styles.card}>
        <Emblem id={g.emblem} size={104} testID="gang-emblem" />
        <GoldTitle size={26} center testID="gang-name">{g.name}</GoldTitle>
        <T w="bold" size={13} color={g.online ? arena.online : arena.muted}>{g.online} online now</T>
      </Panel>
      <View style={styles.row}>
        <RaisedButton testID="gang-add-friends" label="Add friends" icon="friends" disabled={g.members.length >= g.max} onPress={() => { setNote(""); setSheet("add"); }} style={styles.flex} />
        <RaisedButton testID="gang-more" tone="wine" label={g.is_leader ? "Manage" : "Leave / Report"} onPress={() => setSheet("more")} style={styles.flex} />
      </View>
      <ErrorBox testID="gang-action-error" error={sheet ? "" : error} />

      <SectionTitle title={`Members (${g.members.length})`} />
      {g.members.map((m: any) => <PersonRow key={m.pid} testID={`gang-member-${m.pid}`} p={m} sub={`${m.leader ? "Leader · " : ""}Level ${m.level} · ${m.you ? "You" : seenText(m)}`} onPress={() => router.push(go.player(m.pid))}
        right={g.is_leader && !m.you ? <RaisedButton testID={`gang-remove-${m.pid}`} tone="danger" label="Remove" height={40} busy={busy === "rm" + m.pid} disabled={!!busy} style={styles.small}
          onPress={() => act("rm" + m.pid, () => rf(`/gangs/${gid}/members/${m.pid}`, uid, { method: "DELETE" }))} /> : null} />)}

      <SectionTitle title="Last gang matches" />
      {g.recent.map((m: any) => <View key={m.id} testID={`gang-match-${m.id}`} style={styles.match}>
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{m.winner === "Tie" ? "Tie" : `${m.winner} won`} · {m.players} players</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{shortSubject(m.subject)} · {m.chapter || "Mixed"} · {day(m.finished_at)}</T>
        </View>
        {m.you_played ? <RaisedButton testID={`gang-match-open-${m.id}`} tone="wine" label="View" height={40} onPress={() => router.push(go.duel({ review: m.id }))} style={styles.small} /> : null}
      </View>)}
      {!g.recent.length ? <Note testID="gang-matches-empty">No gang match yet. Challenge the gang and start the rivalry!</Note> : null}
    </>}

    <Sheet visible={sheet === "add"} onClose={() => setSheet("")} testID="gang-add-sheet">
      <GoldTitle size={20}>Add your friends</GoldTitle>
      {note ? <T testID="gang-add-note" w="bold" size={13} color={arena.aqua}>{note}</T> : null}
      {addable.map((f) => <PersonRow key={f.pid} testID={`gang-add-row-${f.pid}`} p={f} sub={`Level ${f.level} · ${seenText(f)}`}
        right={<RaisedButton testID={`gang-add-${f.pid}`} label="Add" height={42} busy={busy === "add" + f.pid} disabled={!!busy} onPress={() => add(f.pid, f.name)} style={styles.small} />} />)}
      {friends.data && !addable.length ? <Note testID="gang-add-empty">All your friends are already here. Add more friends from the Gang tab.</Note> : null}
      <ErrorBox testID="gang-add-error" error={error} />
    </Sheet>
    <Sheet visible={sheet === "more"} onClose={() => setSheet("")} testID="gang-more-sheet">
      <GoldTitle size={20}>{g?.name}</GoldTitle>
      {g?.is_leader ? <RaisedButton testID="gang-edit" label="Change name or emblem" onPress={() => { setSheet(""); router.push({ pathname: "/rapid/gang/new", params: { gid, name: g.name, emblem: g.emblem } } as any); }} /> : null}
      <RaisedButton testID="gang-leave" tone="wine" label="Leave gang" busy={busy === "leave"} disabled={!!busy} onPress={() => act("leave", () => rf(`/gangs/${gid}/leave`, uid, { method: "POST", body: {} }), true)} />
      <RaisedButton testID="gang-report" tone="wine" label={note === "reported" ? "Reported ✓" : "Report this gang"} busy={busy === "report"} disabled={!!busy || note === "reported"}
        onPress={() => act("report", async () => { await rf(`/gangs/${gid}/report`, uid, { method: "POST", body: { reason: "Reported from the gang screen" } }); setNote("reported"); })} />
      {g?.is_leader ? <RaisedButton testID="gang-close" tone="danger" label="Close gang for everyone" busy={busy === "close"} disabled={!!busy} onPress={() => act("close", () => rf(`/gangs/${gid}`, uid, { method: "DELETE" }), true)} /> : null}
      <T size={12} color={arena.muted}>{g?.is_leader ? "If you leave, the longest-standing member becomes the leader." : "You can be added again by a friend in this gang."}</T>
      <ErrorBox testID="gang-more-error" error={error} />
    </Sheet>
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, row: { flexDirection: "row", gap: 10 }, small: { width: 92 },
  card: { alignItems: "center", gap: 4, padding: 18 },
  match: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
});

export default withRapid(Gang);

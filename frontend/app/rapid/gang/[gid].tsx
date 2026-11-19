import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, TextInput, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { RF_BASE, rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate, useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Emblem } from "@/src/rapid/Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle, arenaInput } from "@/src/rapid/arena";
import { InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, Sheet, withRapid } from "@/src/rapid/ui";
import { scopeLabel, useScope } from "@/src/rapid/scope";
import { go, sendChallenge, sendWhatsApp, seenText, shortSubject, useFriends } from "@/src/rapid/social";

type Rival = { id: string; name: string; emblem: string; kind: string; members: number; wins: number; losses: number; ties: number };

/** Find a rival gang by its name or gang code, and send the Gang War: my gang against theirs, up to 5 a side. */
function WarSheet({ uid, gid, onClose, visible }: { uid: string; gid: string; onClose: () => void; visible: boolean }) {
  const router = useRouter(), picks = useScope();
  const [q, setQ] = useState(""), [found, setFound] = useState<Rival[] | null>(null), [busy, setBusy] = useState(""), [error, setError] = useState("");
  const rows = q.trim().length < 2 ? null : found;
  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) return;
    let live = true;
    const t = setTimeout(() => { rf<{ items: Rival[] }>(`/gangs/search?q=${encodeURIComponent(term)}`, uid).then((r) => { if (live) setFound(r.items.filter((x) => x.id !== gid)); }).catch((e) => { if (live) setError(e.message); }); }, 350);
    return () => { live = false; clearTimeout(t); };
  }, [q, uid, gid]);
  const war = async (rival: Rival) => {
    setBusy(rival.id); setError("");
    try { const room = await sendChallenge(uid, { gang_id: gid, rival_gang_id: rival.id, picks }); onClose(); router.push(go.room(room)); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  return <Sheet visible={visible} onClose={onClose} testID="gang-war-sheet">
    <GoldTitle size={22}>Gang War</GoldTitle>
    <T size={13} color={arena.muted}>Your gang against another gang, up to 5 a side, on {scopeLabel(picks)}. Rivals don’t need to be your friends.</T>
    <TextInput testID="gang-war-search" value={q} onChangeText={setQ} placeholder="Rival gang name or code (G…)" placeholderTextColor={arena.faint} autoCorrect={false} style={arenaInput} />
    {rows?.map((g) => <View key={g.id} testID={`gang-war-row-${g.id}`} style={styles.match}>
      <Emblem id={g.emblem} size={44} />
      <View style={styles.flex}>
        <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{g.name}</T>
        <T w="bold" size={11} color={arena.muted}>{g.members} members · {g.wins}W {g.losses}L {g.ties}T</T>
      </View>
      <RaisedButton testID={`gang-war-send-${g.id}`} label="Battle" height={42} busy={busy === g.id} disabled={!!busy || !picks.length} onPress={() => war(g)} style={styles.small} />
    </View>)}
    {!picks.length ? <Note testID="gang-war-no-subject">Pick your subjects first: tap Subjects on the Rapid Fire lobby.</Note> : null}
    {rows && !rows.length ? <Note testID="gang-war-empty">No gang found. Ask the rival leader for their gang code.</Note> : null}
    <ErrorBox testID="gang-war-error" error={error} />
  </Sheet>;
}

const day = (iso?: string) => (iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");

/** A gang's own screen: who is in it, one button to challenge everybody, its last matches, and the leader's controls. */
function Gang() {
  const { gid } = useLocalSearchParams<{ gid: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const q = useCached<any>(uid && gid ? `u.${uid}.rfgang.${gid}` : null, () => rf(`/gangs/${gid}`, uid), false);
  const friends = useFriends(uid);
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [note, setNote] = useState("");
  const [sheet, setSheet] = useState<"" | "add" | "more" | "war">("");
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
        <T w="bold" size={13} color={g.online ? arena.online : arena.muted}>{g.kind === "batch" ? "Coaching batch · " : ""}{g.online} online now</T>
        <View style={styles.record} testID="gang-record">
          {([["WINS", g.record.wins], ["LOSSES", g.record.losses], ["TIES", g.record.ties]] as const).map(([k, v]) => <View key={k} style={styles.stat}><T w="heavy" size={20} color={arena.gold}>{v}</T><T w="bold" size={9} color={arena.muted}>{k}</T></View>)}
        </View>
        <T testID="gang-code" w="bold" size={11} color={arena.aqua}>Gang code {g.id} · rivals use it to find you</T>
      </Panel>
      <View style={styles.row}>
        <RaisedButton testID="gang-war" icon="gang" label="GANG WAR" sub="vs another gang" height={56} onPress={() => setSheet("war")} style={styles.flex} />
        <RaisedButton testID="gang-invite-link" tone="wine" glyph="whatsapp" label="Invite link" sub={g.kind === "batch" ? "anyone can join" : "for friends of members"} height={56}
          onPress={() => sendWhatsApp(`Join ${g.name} on JEELIVE.AI Rapid Fire and battle other gangs with us!\n${RF_BASE}/g/${g.id}/${g.invite_code}`)} style={styles.flex} />
      </View>
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
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{m.battle ? `${m.battle.won ? "WON" : m.battle.us === m.battle.them ? "TIE" : "LOST"} ${m.battle.us}–${m.battle.them} vs ${m.battle.rival}` : `${m.winner === "Tie" ? "Tie" : `${m.winner} won`} · ${m.players} players`}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{shortSubject(m.subject)} · {m.chapter || "Mixed"} · {day(m.finished_at)}</T>
        </View>
        {m.you_played ? <RaisedButton testID={`gang-match-open-${m.id}`} tone="wine" label="View" height={40} onPress={() => router.push(go.duel({ review: m.id }))} style={styles.small} /> : null}
      </View>)}
      {!g.recent.length ? <Note testID="gang-matches-empty">No gang match yet. Challenge the gang and start the rivalry!</Note> : null}
    </>}

    {g ? <WarSheet uid={uid} gid={gid} visible={sheet === "war"} onClose={() => setSheet("")} /> : null}
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
  record: { flexDirection: "row", gap: 8, marginTop: 6 }, stat: { width: 76, alignItems: "center", paddingVertical: 6, borderRadius: 14, backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.rim },
  match: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
});

export default withRapid(Gang);

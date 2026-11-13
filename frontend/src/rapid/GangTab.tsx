import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { Icon, T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, Emblem, GameIcon } from "./Art";
import { CloseButton, GoldTitle, Panel, RaisedButton, SectionTitle, arenaInput } from "./arena";
import { Jelly, Pop } from "./juice";
import { FriendFeed } from "./FriendFeed";
import { Face, Note, PersonRow } from "./parts";
import { ErrorBox } from "./ui";
import { go, inviteLink, refreshInbox, seenText, sendWhatsApp, useFriends, useGangs, useInbox } from "./social";

/** Gang tab: your gangs and friends in one place. Search, add, invite, see who added you, and challenge in one tap. */
export function GangTab() {
  const router = useRouter(), uid = useAuth().user?.id || "";
  const inbox = useInbox(), friends = useFriends(uid), gangs = useGangs(uid);
  const [q, setQ] = useState(""), [hits, setHits] = useState<any[] | null>(null), [searching, setSearching] = useState(false);
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const reloads = [friends.reload, gangs.reload];
  useFocusEffect(useCallback(() => { reloads.forEach((f) => f()); if (uid) refreshInbox(uid); }, [...reloads, uid])); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) { setHits(null); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      try { setHits((await rf<any>(`/players/search?q=${encodeURIComponent(term)}`, uid)).items); setError(""); }
      catch (e: any) { setError(e.message); }
      finally { setSearching(false); }
    }, 350);
    return () => clearTimeout(timer);
  }, [q, uid]);

  const act = async (key: string, run: () => Promise<unknown>) => {
    setBusy(key); setError("");
    try { await run(); friends.reload(); gangs.reload(); await refreshInbox(uid); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const add = (pid: string) => act("add" + pid, async () => { await rf("/friends", uid, { method: "POST", body: { pid } }); setHits((rows) => rows?.map((r) => (r.pid === pid ? { ...r, friend: true } : r)) || null); });
  const mine = friends.data?.items || [], myGangs = gangs.data?.items || [];

  return <ScrollView testID="arena-gang" keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <GoldTitle size={24}>Gang & Friends</GoldTitle>
    <View style={styles.search}>
      <Icon name="magnify" size={22} color={arena.aqua} />
      <TextInput testID="rf-player-search" accessibilityLabel="Search players" value={q} onChangeText={setQ} placeholder="Search a name or full phone number" placeholderTextColor={arena.faint} autoCorrect={false} style={styles.input} />
      {searching ? <ActivityIndicator color={arena.aqua} /> : q ? <CloseButton testID="rf-player-search-clear" label="Clear search" onPress={() => setQ("")} /> : null}
    </View>
    <ErrorBox testID="rf-gang-error" error={error || friends.error || gangs.error} retry={() => { friends.reload(); gangs.reload(); }} />

    {hits ? <View style={styles.list} testID="rf-search-results">
      {hits.map((p) => <PersonRow key={p.pid} testID={`rf-search-row-${p.pid}`} p={p} sub={`Level ${p.level} · ${seenText(p)}`} onPress={() => router.push(go.player(p.pid))}
        right={p.friend ? <T testID={`rf-search-friend-${p.pid}`} w="heavy" size={12} color={arena.gold}>Friends ✓</T> : <RaisedButton testID={`rf-search-add-${p.pid}`} label="Add" height={42} busy={busy === "add" + p.pid} disabled={!!busy} onPress={() => add(p.pid)} style={styles.small} />} />)}
      {!hits.length && !searching ? <Note testID="rf-search-empty">Nobody found. Names match partly; phone numbers must be complete.</Note> : null}
    </View> : <>
      {(inbox?.notices || []).map((n) => <Pop key={n.id}><Panel gold testID={`rf-notice-${n.kind}`} style={styles.notice}>
        <View style={styles.noticeRow}>
          {n.kind === "gang_added" && n.gang ? <Emblem id={n.gang.emblem} size={44} /> : <Face p={n.from} size={44} onPress={() => router.push(go.player(n.from.pid))} />}
          <T w="heavy" size={14} color={arena.text} style={styles.flex}>{n.kind === "gang_added" && n.gang ? `${n.from.name} added you to ${n.gang.name}` : `${n.from.name} added you as a friend`}</T>
        </View>
        <View style={styles.noticeRow}>
          {n.kind === "gang_added" && n.gang ? <>
            <RaisedButton testID="rf-notice-leave" label="Leave" tone="wine" height={42} busy={busy === "leave" + n.id} disabled={!!busy} onPress={() => act("leave" + n.id, () => rf(`/gangs/${n.gang!.id}/leave`, uid, { method: "POST", body: {} }))} style={styles.flex} />
            <RaisedButton testID="rf-notice-view" label="View gang" height={42} disabled={!!busy} onPress={() => { const gid = n.gang!.id; act("view" + n.id, () => rf(`/notices/${n.id}/dismiss`, uid, { method: "POST", body: {} })); router.push(go.gang(gid)); }} style={styles.flex} />
          </> : <>
            <RaisedButton testID="rf-notice-dismiss" label="Not now" tone="wine" height={42} busy={busy === "dismiss" + n.id} disabled={!!busy} onPress={() => act("dismiss" + n.id, () => rf(`/notices/${n.id}/dismiss`, uid, { method: "POST", body: {} }))} style={styles.flex} />
            <RaisedButton testID="rf-notice-add-back" label="Add back" height={42} busy={busy === "add" + n.from.pid} disabled={!!busy} onPress={() => add(n.from.pid)} style={styles.flex} />
          </>}
        </View>
      </Panel></Pop>)}

      <View style={styles.actions}>
        <Jelly testID="rf-new-gang" accessibilityLabel="New gang" onPress={() => router.push("/rapid/gang/new" as any)} style={styles.action}>
          <Alive kind="hop" delay={400}><GameIcon name="gang" size={50} /></Alive><T w="heavy" size={12} color={arena.text}>New gang</T>
        </Jelly>
        <Jelly testID="rf-pick-friends" accessibilityLabel="Challenge several friends" onPress={() => router.push(go.challenge())} style={styles.action}>
          <Alive kind="hop" delay={1400}><GameIcon name="swords" size={50} /></Alive><T w="heavy" size={12} color={arena.text}>Challenge</T>
        </Jelly>
        <Jelly testID="rf-invite-link" accessibilityLabel="Invite a friend on WhatsApp" onPress={() => { if (inbox?.me.pid) sendWhatsApp(`Add me on JEECIRCLE.AI Rapid Fire and let’s see who is faster! ${inviteLink(inbox.me.pid)}`); }} style={styles.action}>
          <Alive kind="hop" delay={2400}><GameIcon name="friends" size={50} /></Alive><T w="heavy" size={12} color={arena.text}>Invite link</T>
        </Jelly>
      </View>

      <FriendFeed uid={uid} hasFriends={mine.length > 0} />

      <SectionTitle title={`My gangs${myGangs.length ? ` (${myGangs.length})` : ""}`} />
      <View style={styles.list}>
        {myGangs.map((g) => <View key={g.id} testID={`rf-gang-row-${g.id}`} style={styles.gang}>
          <Jelly testID={`rf-gang-open-${g.id}`} accessibilityLabel={`Open ${g.name}`} onPress={() => router.push(go.gang(g.id))} style={styles.gangMain}>
            <Emblem id={g.emblem} size={50} />
            <View style={styles.flex}>
              <T w="heavy" size={15} color={arena.text} numberOfLines={1}>{g.name}</T>
              <T w="bold" size={12} color={g.online ? arena.online : arena.muted}>{g.members} member{g.members === 1 ? "" : "s"} · {g.online} online</T>
            </View>
          </Jelly>
          <RaisedButton testID={`rf-gang-challenge-${g.id}`} label="Challenge" height={42} disabled={g.members < 2} onPress={() => router.push(go.challenge({ gang: g.id }))} style={styles.medium} />
        </View>)}
        {gangs.data && !myGangs.length ? <Note testID="rf-gangs-empty">No gang yet. Start one and challenge everybody in one tap!</Note> : null}
      </View>

      <SectionTitle title={`Friends${mine.length ? ` (${mine.length})` : ""}`} />
      <View style={styles.list} testID="rf-friends-list">
        {mine.map((f) => <PersonRow key={f.pid} testID={`rf-friend-row-${f.pid}`} p={f} sub={`Level ${f.level} · ${seenText(f)}`} onPress={() => router.push(go.player(f.pid))}
          right={<RaisedButton testID={`rf-friend-challenge-${f.pid}`} label="Challenge" height={42} onPress={() => router.push(go.challenge({ pid: f.pid }))} style={styles.medium} />} />)}
        {friends.data && !mine.length ? <Note testID="rf-friends-empty">No friends yet. Search above, or send your invite link on WhatsApp.</Note> : null}
        {!friends.data && friends.loading ? <ActivityIndicator color={arena.aqua} /> : null}
      </View>
    </>}
  </ScrollView>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 28, gap: 12 }, list: { gap: 8 },
  search: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 54, paddingLeft: 14, paddingRight: 6, borderRadius: 18, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  input: { ...arenaInput, flex: 1, height: 50, borderWidth: 0, paddingHorizontal: 0, backgroundColor: arena.clear, fontSize: 15 },
  small: { width: 76 }, medium: { width: 112 },
  notice: { padding: 12, gap: 10 }, noticeRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  actions: { flexDirection: "row", gap: 10 },
  action: { flex: 1, minHeight: 92, alignItems: "center", justifyContent: "center", gap: 2, borderRadius: 20, backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 6, borderBottomColor: arena.panelEdge },
  gang: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 68, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  gangMain: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 12, minHeight: 50 },
});

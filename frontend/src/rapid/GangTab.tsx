import React, { useCallback, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, Emblem, GameIcon } from "./Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "./arena";
import { Jelly, Pop } from "./juice";
import { FriendCodeBox } from "./FriendCodeBox";
import { FriendFeed } from "./FriendFeed";
import { Face, Note, PersonRow } from "./parts";
import { ErrorBox } from "./ui";
import { gangNotices, go, refreshInbox, seenText, shareFriendCode, useFriendCode, useFriends, useGangs, useInbox } from "./social";

/** Gang tab: your gangs and friends in one place. Add a friend with a Friend Code, see who added you, and challenge in one tap. */
export function GangTab() {
  const router = useRouter(), uid = useAuth().user?.id || "";
  const inbox = useInbox(), friends = useFriends(uid), gangs = useGangs(uid), myCode = useFriendCode(uid).data?.code;
  const [busy, setBusy] = useState(""), [error, setError] = useState("");
  const narrow = useWindowDimensions().width < 360; // small phones: an icon-only Challenge button leaves room for the name and crown
  const { reload: reloadFriends } = friends, { reload: reloadGangs } = gangs;
  useFocusEffect(useCallback(() => { reloadFriends(); reloadGangs(); if (uid) refreshInbox(uid); }, [reloadFriends, reloadGangs, uid]));

  const act = async (key: string, run: () => Promise<unknown>) => {
    setBusy(key); setError("");
    try { await run(); friends.reload(); gangs.reload(); await refreshInbox(uid); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const dismiss = (id: string) => rf(`/notices/${id}/dismiss`, uid, { method: "POST", body: {} });
  const mine = friends.data?.items || [], myGangs = gangs.data?.items || [];

  return <ScrollView testID="arena-gang" keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    <GoldTitle size={24}>Gang & Friends</GoldTitle>
    <FriendCodeBox uid={uid} onAdded={() => { friends.reload(); refreshInbox(uid); }} onOpen={(pid) => router.push(go.player(pid))} />
    <ErrorBox testID="rf-gang-error" error={error || friends.error || gangs.error} retry={() => { friends.reload(); gangs.reload(); }} />

    <>
      {gangNotices(inbox).map((n) => <Pop key={n.id}><Panel gold testID={`rf-notice-${n.kind}`} style={styles.notice}>
        <View style={styles.noticeRow}>
          {n.kind === "gang_added" && n.gang ? <Emblem id={n.gang.emblem} size={44} /> : <Face p={n.from} size={44} onPress={() => router.push(go.player(n.from.pid))} />}
          <T w="heavy" size={14} color={arena.text} style={styles.flex}>{n.kind === "gang_added" && n.gang ? `${n.from.name} added you to ${n.gang.name}` : n.via === "link" ? `${n.from.name} joined your match link. You are friends now!` : `${n.from.name} added you with your Friend Code. You are friends now!`}</T>
        </View>
        <View style={styles.noticeRow}>
          {n.kind === "gang_added" && n.gang ? <>
            <RaisedButton testID="rf-notice-leave" label="Leave" tone="wine" height={42} busy={busy === "leave" + n.id} disabled={!!busy} onPress={() => act("leave" + n.id, () => rf(`/gangs/${n.gang!.id}/leave`, uid, { method: "POST", body: {} }))} style={styles.flex} />
            <RaisedButton testID="rf-notice-view" label="View gang" height={42} disabled={!!busy} onPress={() => { const gid = n.gang!.id; act("view" + n.id, () => dismiss(n.id)); router.push(go.gang(gid)); }} style={styles.flex} />
          </> : <>
            <RaisedButton testID="rf-notice-dismiss" label="OK" tone="wine" height={42} busy={busy === "dismiss" + n.id} disabled={!!busy} onPress={() => act("dismiss" + n.id, () => dismiss(n.id))} style={styles.flex} />
            <RaisedButton testID="rf-notice-challenge" label="Challenge" icon="swords" height={42} disabled={!!busy} onPress={() => { const pid = n.from.pid; act("go" + n.id, () => dismiss(n.id)); router.push(go.challenge({ pid })); }} style={styles.flex} />
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
        <Jelly testID="rf-share-code" accessibilityLabel="Send your Friend Code on WhatsApp" disabled={!myCode} onPress={() => { if (myCode) shareFriendCode(myCode); }} style={styles.action}>
          <Alive kind="hop" delay={2400}><GameIcon name="friends" size={50} /></Alive><T w="heavy" size={12} color={arena.text}>Invite</T>
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
          right={narrow ? <RaisedButton testID={`rf-friend-challenge-${f.pid}`} icon="swords" height={44} accessibilityLabel={`Challenge ${f.name}`} onPress={() => router.push(go.challenge({ pid: f.pid }))} style={styles.iconBtn} />
            : <RaisedButton testID={`rf-friend-challenge-${f.pid}`} label="Challenge" height={42} onPress={() => router.push(go.challenge({ pid: f.pid }))} style={styles.medium} />} />)}
        {friends.data && !mine.length ? <Note testID="rf-friends-empty">No friends yet. Send your Friend Code on WhatsApp, or enter a friend’s code above.</Note> : null}
        {!friends.data && friends.loading ? <ActivityIndicator color={arena.aqua} /> : null}
      </View>
    </>
  </ScrollView>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 28, gap: 12 }, list: { gap: 8 },
  medium: { width: 112 }, iconBtn: { width: 52 },
  notice: { padding: 12, gap: 10 }, noticeRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  actions: { flexDirection: "row", gap: 10 },
  action: { flex: 1, minHeight: 92, alignItems: "center", justifyContent: "center", gap: 2, borderRadius: 20, backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.rim, borderBottomWidth: 6, borderBottomColor: arena.panelEdge },
  gang: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 68, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  gangMain: { flex: 1, minWidth: 0, flexDirection: "row", alignItems: "center", gap: 12, minHeight: 50 },
});

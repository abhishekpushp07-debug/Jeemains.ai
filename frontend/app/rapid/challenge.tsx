import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { rf, uuid } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { ChapterSheet } from "@/src/components/ChapterSheet";
import { arena } from "@/src/theme";
import { Emblem } from "@/src/rapid/Art";
import { Panel, RaisedButton, Ribbon, SectionTitle, arenaInput } from "@/src/rapid/arena";
import { Jelly } from "@/src/rapid/juice";
import { Check, InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { go, seenText, selection, sendChallenge, setArenaTab, shortSubject, useFriends, useGangs } from "@/src/rapid/social";

const MAX_FRIENDS = 4;

/** Play Friends: pick one gang or up to 4 friends, check the subject, and send. The old 6-letter code stays as a backup. */
function Challenge() {
  const params = useLocalSearchParams<{ pid?: string; gang?: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const friends = useFriends(uid), gangs = useGangs(uid);
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const [subject, setSubject] = useState(selection.subject), [chapter, setChapter] = useState(selection.chapter);
  const [picked, setPicked] = useState<string[]>(params.pid ? [params.pid] : []);
  const [gang, setGang] = useState(params.gang || "");
  const [sheet, setSheet] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [code, setCode] = useState("");
  const myFriends = friends.data?.items || [], myGangs = gangs.data?.items || [];

  const toggle = (pid: string) => { setGang(""); setPicked((now) => (now.includes(pid) ? now.filter((x) => x !== pid) : now.length < MAX_FRIENDS ? [...now, pid] : now)); };
  const send = async () => {
    setBusy(true); setError("");
    try { router.replace(go.room(await sendChallenge(uid, gang ? { gang_id: gang, subject, chapter } : { pids: picked, subject, chapter }))); }
    catch (e: any) { setError(e.message); setBusy(false); }
  };
  const label = chapter || `Mixed ${shortSubject(subject)}`;

  return <InnerScreen testID="challenge-screen" title="Play Friends" sub="One gang, or up to 4 friends"
    footer={<><ErrorBox testID="challenge-error" error={error} />
      <RaisedButton testID="challenge-send" icon="swords" height={62} streak busy={busy} disabled={!gang && !picked.length}
        label={gang ? "CHALLENGE GANG" : picked.length > 1 ? `CHALLENGE ${picked.length} FRIENDS` : "SEND CHALLENGE"} sub={label} onPress={send} /></>}>
    <Ribbon testID="challenge-chapter" label={label} sub={`${shortSubject(subject)} · tap to change`} onPress={() => setSheet(true)} />

    {myGangs.length ? <SectionTitle title="Your gangs" /> : null}
    {myGangs.map((g) => {
      const on = gang === g.id;
      return <Jelly key={g.id} testID={`challenge-gang-${g.id}`} accessibilityLabel={`${g.name}, ${g.members} members`} accessibilityState={{ selected: on }} disabled={g.members < 2}
        onPress={() => { setPicked([]); setGang(on ? "" : g.id); }} style={[styles.gang, on && styles.on]}>
        <Emblem id={g.emblem} size={48} />
        <View style={styles.flex}>
          <T w="heavy" size={15} color={arena.text} numberOfLines={1}>{g.name}</T>
          <T w="bold" size={12} color={g.online ? arena.online : arena.muted}>{g.members < 2 ? "Add members first" : `${g.members} members · ${g.online} online`}</T>
        </View>
        <Check on={on} />
      </Jelly>;
    })}

    <SectionTitle title={`Friends${picked.length ? ` (${picked.length}/${MAX_FRIENDS})` : ""}`} />
    {!friends.data && friends.loading ? <ActivityIndicator color={arena.aqua} /> : null}
    {myFriends.map((f) => <PersonRow key={f.pid} testID={`challenge-friend-${f.pid}`} p={f} sub={`Level ${f.level} · ${seenText(f)}`} selected={picked.includes(f.pid)} onPress={() => toggle(f.pid)} right={<Check on={picked.includes(f.pid)} />} />)}
    {friends.data && !myFriends.length ? <>
      <Note testID="challenge-empty">No friends yet. Add a friend first, then challenge them in one tap.</Note>
      <RaisedButton testID="challenge-find-friends" label="Find friends" icon="friends" onPress={() => { setArenaTab("gang"); router.navigate("/(tabs)/rapid"); }} />
    </> : null}
    <ErrorBox testID="challenge-load-error" error={friends.error || gangs.error} retry={() => { friends.reload(); gangs.reload(); }} />

    <SectionTitle title="Play with a code" />
    <Panel flat style={styles.codeBox}>
      <T size={12} color={arena.muted}>The 6-letter code still works for a 1 v 1 with anyone.</T>
      <View style={styles.row}>
        <TextInput testID="challenge-code-input" accessibilityLabel="Duel code" value={code} onChangeText={(v) => setCode(v.toUpperCase())} placeholder="CODE" placeholderTextColor={arena.faint}
          autoCapitalize="characters" autoCorrect={false} maxLength={8} style={[arenaInput, styles.flex, styles.codeInput]} />
        <RaisedButton testID="challenge-code-join" label="Join" disabled={code.trim().length < 4} onPress={() => router.push(go.duel({ mode: "join", code: code.trim(), r: uuid() }))} style={styles.join} />
      </View>
      <RaisedButton testID="challenge-code-create" tone="wine" label="Create a code to share" onPress={() => router.push(go.duel({ mode: "invite", subject, chapter, r: uuid() }))} />
    </Panel>

    <ChapterSheet visible={sheet} onClose={() => setSheet(false)} subjects={cat.data?.subjects || []} subject={subject} chapter={chapter} recent={[]}
      onPick={(s, ch) => { setSubject(s); setChapter(ch); Object.assign(selection, { subject: s, chapter: ch }); setSheet(false); }} />
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, row: { flexDirection: "row", alignItems: "center", gap: 10 },
  gang: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 68, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  on: { borderColor: arena.tealHi, backgroundColor: arena.panelHi },
  codeBox: { padding: 12, gap: 10 }, codeInput: { letterSpacing: 4, textAlign: "center" }, join: { width: 92 },
});

export default withRapid(Challenge);

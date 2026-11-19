import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Emblem } from "@/src/rapid/Art";
import { Panel, RaisedButton, Ribbon, SectionTitle } from "@/src/rapid/arena";
import { Jelly } from "@/src/rapid/juice";
import { Check, InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { ScopeSheet } from "@/src/rapid/ScopeSheet";
import { scopeLabel, scopeSubjects, setScope, useCardCount, useScope } from "@/src/rapid/scope";
import { go, seenText, sendChallenge, setArenaTab, shareRoom, useFriends, useGangs } from "@/src/rapid/social";

const MAX_FRIENDS = 4;

/** Play Friends: share a match link on WhatsApp (anyone can join and becomes your friend), or pick one gang or up to 4 friends. */
function Challenge() {
  const params = useLocalSearchParams<{ pid?: string; gang?: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const friends = useFriends(uid), gangs = useGangs(uid);
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const picks = useScope();
  const [picked, setPicked] = useState<string[]>(params.pid ? [params.pid] : []);
  const [gang, setGang] = useState(params.gang || "");
  const [sheet, setSheet] = useState(false), [busy, setBusy] = useState<"" | "send" | "link">(""), [error, setError] = useState("");
  const myFriends = friends.data?.items || [], myGangs = gangs.data?.items || [];

  const toggle = (pid: string) => { setGang(""); setPicked((now) => (now.includes(pid) ? now.filter((x) => x !== pid) : now.length < MAX_FRIENDS ? [...now, pid] : now)); };
  const send = async (link: boolean) => {
    setBusy(link ? "link" : "send"); setError("");
    try {
      const room = await sendChallenge(uid, { ...(gang ? { gang_id: gang } : { pids: picked }), picks, ...(link ? { link: true } : {}) });
      router.replace(go.room(room));
      if (link) shareRoom(room, label);
    } catch (e: any) { setError(e.message); setBusy(""); }
  };
  const label = scopeLabel(picks), count = useCardCount();
  const invites = gang ? "your gang" : picked.length ? `${picked.length} friend${picked.length > 1 ? "s" : ""}` : "";

  return <InnerScreen testID="challenge-screen" title="Play Friends" sub="A WhatsApp link, one gang, or up to 4 friends"
    footer={<><ErrorBox testID="challenge-error" error={error} />
      <RaisedButton testID="challenge-send" icon="swords" height={62} streak busy={busy === "send"} disabled={(!gang && !picked.length) || !!busy}
        label={gang ? "CHALLENGE GANG" : picked.length > 1 ? `CHALLENGE ${picked.length} FRIENDS` : "SEND CHALLENGE"} sub={label} onPress={() => send(false)} /></>}>
    <Ribbon testID="challenge-chapter" label={label} sub={`${scopeSubjects(picks)} · ${count} cards · tap to change`} onPress={() => setSheet(true)} />

    <Panel gold testID="challenge-link" style={styles.link}>
      <View style={styles.linkTop}>
        <View style={styles.wa}><Icon name="whatsapp" size={26} color={arena.text} /></View>
        <View style={styles.flex}>
          <T w="heavy" size={15} color={arena.gold}>Share a match link</T>
          <T w="bold" size={12} color={arena.text}>Anyone with the link takes a seat, in the app or a browser. Whoever joins becomes your friend.</T>
        </View>
      </View>
      <RaisedButton testID="challenge-share-link" glyph="whatsapp" height={54} label="SHARE MATCH LINK" busy={busy === "link"} disabled={!!busy}
        sub={invites ? `Up to 4 players · ${invites} invited too` : "Up to 4 players join you"} onPress={() => send(true)} />
    </Panel>

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
      <Note testID="challenge-empty">No friends yet? Share a match link above. Everyone who joins from it becomes your friend.</Note>
      <RaisedButton testID="challenge-find-friends" label="Find friends" icon="friends" onPress={() => { setArenaTab("gang"); router.navigate("/(tabs)/rapid"); }} />
    </> : null}
    <ErrorBox testID="challenge-load-error" error={friends.error || gangs.error} retry={() => { friends.reload(); gangs.reload(); }} />

    <ScopeSheet visible={sheet} onClose={() => setSheet(false)} subjects={cat.data?.subjects || []} value={picks} onDone={setScope} />
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  link: { padding: 12, gap: 10 }, linkTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  wa: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline },
  gang: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 68, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  on: { borderColor: arena.tealHi, backgroundColor: arena.panelHi },
});

export default withRapid(Challenge);

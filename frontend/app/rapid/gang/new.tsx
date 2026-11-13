import React, { useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { EMBLEM_IDS, Emblem } from "@/src/rapid/Art";
import { RaisedButton, SectionTitle, Segment, arenaInput } from "@/src/rapid/arena";
import { Jelly } from "@/src/rapid/juice";
import { Check, InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { go, seenText, useFriends } from "@/src/rapid/social";

/** Start a gang (name, emblem, friends), or change the name and emblem of one you lead (`gid` given). */
function GangForm() {
  const edit = useLocalSearchParams<{ gid?: string; name?: string; emblem?: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const friends = useFriends(uid);
  const [name, setName] = useState(edit.name || ""), [emblem, setEmblem] = useState(edit.emblem || "lion");
  const [picked, setPicked] = useState<string[]>([]), [kind, setKind] = useState<"gang" | "batch">("gang");
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const myFriends = friends.data?.items || [];

  const save = async () => {
    setBusy(true); setError("");
    try {
      if (edit.gid) { await rf(`/gangs/${edit.gid}`, uid, { method: "PATCH", body: { name: name.trim(), emblem } }); invalidate(`u.${uid}.rfgangs`); router.back(); return; }
      const made = await rf<any>("/gangs", uid, { method: "POST", body: { name: name.trim(), emblem, kind, pids: picked } });
      invalidate(`u.${uid}.rfgangs`);
      router.replace(go.gang(made.id));
    } catch (e: any) { setError(e.message); setBusy(false); }
  };

  return <InnerScreen testID="gang-form-screen" title={edit.gid ? "Edit gang" : "New gang"} sub={edit.gid ? "Name and emblem" : "Name it, pick an emblem, bring your friends"}
    footer={<><ErrorBox testID="gang-form-error" error={error} />
      <RaisedButton testID="gang-form-save" height={60} label={edit.gid ? "SAVE" : "CREATE GANG"} icon="gang" busy={busy} disabled={name.trim().length < 2} onPress={save} /></>}>
    <View style={styles.preview}>
      <Emblem id={emblem} size={96} testID="gang-form-preview" />
      <T w="heavy" size={20} color={arena.gold} numberOfLines={1}>{name.trim() || "Your gang"}</T>
    </View>
    <TextInput testID="gang-form-name" accessibilityLabel="Gang name" value={name} onChangeText={setName} maxLength={20} placeholder="Gang name (up to 20 letters)" placeholderTextColor={arena.faint} autoCorrect={false} style={arenaInput} />
    {edit.gid ? null : <>
      <Segment prefix="gang-form-kind" value={kind} onChange={setKind} items={[["gang", "Gang · friends"], ["batch", "Batch · class"]]} />
      <T testID="gang-form-kind-note" size={12} color={arena.muted} style={styles.center}>{kind === "batch" ? "Up to 200 classmates. Anyone with the batch link can join." : "A circle of friends. The link works for friends of a member."}</T>
    </>}

    <SectionTitle title="Emblem" />
    <View style={styles.grid}>
      {EMBLEM_IDS.map((id) => <Jelly key={id} testID={`gang-form-emblem-${id}`} accessibilityLabel={`${id} emblem`} accessibilityState={{ selected: emblem === id }} onPress={() => setEmblem(id)} style={[styles.cell, emblem === id && styles.cellOn]}>
        <Emblem id={id} size={56} />
      </Jelly>)}
    </View>

    {edit.gid ? null : <>
      <SectionTitle title={`Add friends${picked.length ? ` (${picked.length})` : ""}`} />
      {myFriends.map((f) => {
        const on = picked.includes(f.pid);
        return <PersonRow key={f.pid} testID={`gang-form-friend-${f.pid}`} p={f} sub={`Level ${f.level} · ${seenText(f)}`} selected={on} right={<Check on={on} />}
          onPress={() => setPicked((now) => (on ? now.filter((x) => x !== f.pid) : now.length < 19 ? [...now, f.pid] : now))} />;
      })}
      {friends.data && !myFriends.length ? <Note testID="gang-form-no-friends">No friends yet. You can create the gang now and add friends later.</Note> : null}
    </>}
  </InnerScreen>;
}

const styles = StyleSheet.create({
  preview: { alignItems: "center", gap: 4 }, center: { textAlign: "center" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  cell: { width: "23%", aspectRatio: 1, alignItems: "center", justifyContent: "center", borderRadius: 18, backgroundColor: arena.panel, borderWidth: 2, borderColor: arena.rim },
  cellOn: { borderColor: arena.gold, backgroundColor: arena.panelHi },
});

export default withRapid(GangForm);

import React, { useCallback, useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { Alive, Emblem, GameIcon } from "@/src/rapid/Art";
import { GoldTitle, Panel, RaisedButton, Ribbon, SectionTitle, Segment, arenaInput } from "@/src/rapid/arena";
import { Jelly, Pop, Twinkles } from "@/src/rapid/juice";
import { Check, Face, InnerScreen, Note, PersonRow } from "@/src/rapid/parts";
import { LiveStrip } from "@/src/rapid/LiveStrip";
import { ScopeSheet } from "@/src/rapid/ScopeSheet";
import { cardCount, scopeLabel, scopeSubjects, setScope, useScope } from "@/src/rapid/scope";
import { ErrorBox, withRapid } from "@/src/rapid/ui";
import { clock, cleanCode, go, inboxAge, refreshInbox, seenText, useFriends, useGangs, useInbox } from "@/src/rapid/social";

export const CUP_SIZES = [4, 8, 16] as const;
type Size = (typeof CUP_SIZES)[number];
const ROUNDS: Record<Size, string> = { 4: "Semis → Final", 8: "Quarters → Semis → Final", 16: "Round of 16 → Final" };
const CUP_CARDS = 15;

/** A tiny bracket: the dots of every round, narrowing to one champion. */
function MiniBracket({ size, on }: { size: Size; on: boolean }) {
  const cols: number[] = [];
  for (let n = size; n >= 1; n /= 2) cols.push(n);
  const dot = size === 16 ? 3 : size === 8 ? 5 : 6;
  return <View style={styles.mini}>{cols.map((n, k) => <View key={k} style={styles.miniCol}>
    {Array.from({ length: n }, (_, i) => <View key={i} style={[styles.dot, { width: dot, height: dot }, n === 1 && styles.dotGold, on && n > 1 && styles.dotOn]} />)}
  </View>)}</View>;
}

/** Knockout Cup hub: start an Open Cup (anyone, practice rivals fill seats) or a Friends Cup (friends or a gang), 4, 8 or 16 players; join an invite; watch a cup with its code. */
function CupHub() {
  const router = useRouter(), uid = useAuth().user?.id || "";
  const inbox = useInbox(), friends = useFriends(uid), gangs = useGangs(uid), picks = useScope();
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const mine = useCached<any>(uid ? `u.${uid}.rfcups` : null, () => rf("/cups", uid), false);
  const [kind, setKind] = useState<"open" | "private">("open"), [size, setSize] = useState<Size>(4);
  const [picked, setPicked] = useState<string[]>([]), [gang, setGang] = useState("");
  const [sheet, setSheet] = useState(false), [busy, setBusy] = useState(""), [error, setError] = useState(""), [watchError, setWatchError] = useState(""), [code, setCode] = useState("");
  const reload = mine.reload;
  useFocusEffect(useCallback(() => { reload(); if (uid) refreshInbox(uid); }, [reload, uid]));

  const cards = cardCount(picks, cat.data?.subjects), enough = cards >= CUP_CARDS;
  const myFriends = friends.data?.items || [], myGangs = gangs.data?.items || [];
  const toggle = (pid: string) => { setGang(""); setPicked((now) => (now.includes(pid) ? now.filter((x) => x !== pid) : now.length < size - 1 ? [...now, pid] : now)); };
  const run = async (key: string, fn: () => Promise<any>) => {
    const fail = key === "watch" ? setWatchError : setError;
    setBusy(key); setError(""); setWatchError("");
    try { const c = await fn(); refreshInbox(uid); router.push(go.cup(c.id)); }
    catch (e: any) { fail(e.message); }
    finally { setBusy(""); }
  };
  const create = () => run("create", () => rf("/cups", uid, { method: "POST", body: { kind, size, picks, ...(kind === "private" ? (gang ? { gang_id: gang } : { pids: picked }) : {}) } }));
  const ready = enough && (kind === "open" || !!gang || picked.length > 0);
  const label = scopeLabel(picks);

  return <InnerScreen testID="cup-hub" title="Knockout Cup" sub="Win every round. Lift the cup."
    footer={<><ErrorBox testID="cup-hub-error" error={error} />
      <RaisedButton testID="cup-create" icon="swords" height={62} streak busy={busy === "create"} disabled={!ready || !!busy}
        label={kind === "open" ? "FIND A CUP" : "CREATE CUP"} sub={`${size} players · ${label}`} onPress={create} /></>}>
    <Panel gold testID="cup-hero" style={styles.hero}>
      <View><Alive kind="breathe"><GameIcon name="trophy" size={104} /></Alive><Twinkles spots={[[8, 20, 14], [92, 26, 12], [50, 0, 11], [16, 86, 10], [86, 82, 12]]} /></View>
      <GoldTitle size={28} center>KNOCKOUT CUP</GoldTitle>
      <T w="bold" size={12} color={arena.aqua} style={styles.center}>{CUP_CARDS} cards a match · every round starts together · lose once and you’re out</T>
      <View testID="cup-prizes" style={styles.prizes}>
        <View style={styles.prize}><GameIcon name="coin" size={26} /><T w="heavy" size={11} color={arena.gold} style={styles.center}>Win 30 coins{"\n"}+40 per real rival</T></View>
        <View style={styles.prize}><GameIcon name="trophy" size={26} /><T w="heavy" size={11} color={arena.gold} style={styles.center}>Cup Champion{"\n"}trophy</T></View>
      </View>
    </Panel>

    {inbox?.cup ? <Jelly testID="cup-hub-active" accessibilityLabel="Your cup is on. Open it" onPress={() => router.push(go.cup(inbox.cup!))}>
      <Panel style={styles.active}><GameIcon name="trophy" size={44} /><View style={styles.flex}><T w="heavy" size={15} color={arena.gold}>Your cup is on!</T><T w="bold" size={12} color={arena.aqua}>Tap to open the bracket</T></View><GameIcon name="swords" size={36} /></Panel>
    </Jelly> : null}

    {(inbox?.cups || []).map((c) => {
      const left = Math.max(0, Math.round(c.expires_in - inboxAge()));
      return <Pop key={c.id}><Panel gold testID={`cup-invite-${c.id}`} style={styles.invite}>
        <Face p={c.from} size={46} />
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{c.from.name} invited you</T>
          <T w="bold" size={12} color={arena.aqua} numberOfLines={1}>{c.label} · {c.joined}/{c.size} in · {clock(left)}</T>
        </View>
        <RaisedButton testID={`cup-invite-join-${c.id}`} label="Join" height={42} busy={busy === c.id} disabled={!!busy} onPress={() => run(c.id, () => rf(`/cups/${c.id}/join`, uid, { method: "POST", body: {} }))} style={styles.small} />
      </Panel></Pop>;
    })}

    <SectionTitle title="1 · Who plays?" />
    <Segment prefix="cup-kind" value={kind} onChange={(k) => { setKind(k); setError(""); }} items={[["open", "Open · anyone"], ["private", "Friends · invite"]]} />
    <T testID="cup-kind-note" size={12} color={arena.muted} style={styles.center}>{kind === "open" ? "Players from all over join in 40 s. Practice rivals take the empty seats." : "Only friends or one gang you pick. You start it when ready; empty seats become byes."}</T>

    <SectionTitle title="2 · How many players?" />
    <View style={styles.sizes}>
      {CUP_SIZES.map((n) => {
        const on = size === n;
        return <Jelly key={n} testID={`cup-size-${n}`} accessibilityLabel={`${n} players`} accessibilityState={{ selected: on }} onPress={() => { setSize(n); setError(""); setPicked((p) => p.slice(0, n - 1)); }} style={[styles.size, on && styles.sizeOn]}>
          <T w="heavy" size={34} color={on ? arena.gold : arena.text}>{n}</T>
          <T w="heavy" size={10} color={on ? arena.aqua : arena.muted}>PLAYERS</T>
          <MiniBracket size={n} on={on} />
          <T w="bold" size={9.5} color={arena.muted} numberOfLines={2} style={styles.center}>{ROUNDS[n]}</T>
        </Jelly>;
      })}
    </View>

    <SectionTitle title="3 · Battleground" />
    <Ribbon testID="cup-scope" label={label} sub={`${scopeSubjects(picks)} · ${cards} cards · tap to change`} onPress={() => setSheet(true)} />
    {!enough && cat.data ? <T testID="cup-scope-short" w="bold" size={12} color={arena.danger} style={styles.center}>Pick more chapters: a cup match needs {CUP_CARDS} cards.</T> : null}

    {kind === "private" ? <>
      <SectionTitle title={gang ? "Gang" : `Invite friends${picked.length ? ` (${picked.length}/${size - 1})` : ""}`} />
      {myGangs.map((g) => {
        const on = gang === g.id;
        return <Jelly key={g.id} testID={`cup-gang-${g.id}`} accessibilityLabel={`${g.name}, ${g.members} members`} accessibilityState={{ selected: on }} disabled={g.members < 2}
          onPress={() => { setPicked([]); setGang(on ? "" : g.id); }} style={[styles.gang, on && styles.on]}>
          <Emblem id={g.emblem} size={44} />
          <View style={styles.flex}><T w="heavy" size={15} color={arena.text} numberOfLines={1}>{g.name}</T><T w="bold" size={12} color={arena.muted}>{g.members} members · whole gang invited</T></View>
          <Check on={on} />
        </Jelly>;
      })}
      {myFriends.map((f) => <PersonRow key={f.pid} testID={`cup-friend-${f.pid}`} p={f} sub={`Level ${f.level} · ${seenText(f)}`} selected={picked.includes(f.pid)} onPress={() => toggle(f.pid)} right={<Check on={picked.includes(f.pid)} />} />)}
      {friends.data && !myFriends.length && !myGangs.length ? <Note testID="cup-no-friends">Add friends with their Friend Code first, or play an Open Cup.</Note> : null}
    </> : null}

    <SectionTitle title="Watch with a code" />
    <Panel flat style={styles.watch}>
      {watchError ? <ErrorBox testID="cup-watch-error" error={watchError} /> : <T size={12} color={arena.muted}>Got a cup’s 6-letter watch code? Follow its bracket and every live match. Up to 100 people can watch.</T>}
      <View style={styles.row}>
        <TextInput testID="cup-watch-input" accessibilityLabel="Cup watch code" value={code} onChangeText={(v) => { setCode(cleanCode(v)); setWatchError(""); }} placeholder="CODE" placeholderTextColor={arena.faint}
          autoCapitalize="characters" autoCorrect={false} maxLength={6} style={[arenaInput, styles.flex, styles.codeInput]} />
        <RaisedButton testID="cup-watch-go" glyph="eye" label="Watch" busy={busy === "watch"} disabled={code.length !== 6 || !!busy} onPress={() => run("watch", () => rf("/cups/watch", uid, { method: "POST", body: { code } }))} style={styles.watchBtn} />
      </View>
    </Panel>

    <LiveStrip uid={uid} />

    {mine.data?.items?.length ? <>
      <SectionTitle title="Your cups" />
      {mine.data.items.map((c: any) => <Jelly key={c.id} testID={`cup-mine-${c.id}`} accessibilityLabel={`${c.label} cup`} onPress={() => router.push(go.cup(c.id))} style={styles.past}>
        <View style={[styles.result, c.won && styles.resultWon]}><T w="heavy" size={11} color={c.won ? arena.badgeInk : arena.text}>{c.status === "finished" ? (c.won ? "WON" : "OUT") : "LIVE"}</T></View>
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{c.size}-player cup · {c.label}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{c.status === "finished" ? `Champion: ${c.won ? "You" : c.champion || "—"}${c.prize ? ` · +${c.prize} coins` : ""}` : c.status === "open" ? "Filling seats…" : "Rounds in play"}</T>
        </View>
      </Jelly>)}
    </> : null}

    <ScopeSheet visible={sheet} onClose={() => setSheet(false)} subjects={cat.data?.subjects || []} value={picks} onDone={setScope} min={CUP_CARDS} />
  </InnerScreen>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, row: { flexDirection: "row", alignItems: "center", gap: 10 }, small: { width: 84 },
  hero: { alignItems: "center", gap: 6, paddingVertical: 18, paddingHorizontal: 14 },
  prizes: { flexDirection: "row", gap: 8, alignSelf: "stretch", marginTop: 4 },
  prize: { flex: 1, alignItems: "center", justifyContent: "center", gap: 2, paddingVertical: 8, paddingHorizontal: 4, borderRadius: 14, backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.goldDeep },
  active: { flexDirection: "row", alignItems: "center", gap: 12, padding: 12, borderColor: arena.tealHi },
  invite: { flexDirection: "row", alignItems: "center", gap: 10, padding: 12 },
  sizes: { flexDirection: "row", gap: 10 },
  size: { flex: 1, alignItems: "center", gap: 3, paddingVertical: 12, paddingHorizontal: 6, borderRadius: 20, backgroundColor: arena.panel, borderWidth: 2, borderColor: arena.rim, borderBottomWidth: 6, borderBottomColor: arena.panelEdge },
  sizeOn: { borderColor: arena.gold, backgroundColor: arena.panelHi },
  mini: { flexDirection: "row", alignItems: "center", gap: 5, height: 62, marginVertical: 4 },
  miniCol: { height: "100%", justifyContent: "space-around", alignItems: "center" },
  dot: { borderRadius: 4, backgroundColor: arena.rim }, dotOn: { backgroundColor: arena.tealHi }, dotGold: { width: 10, height: 10, borderRadius: 5, backgroundColor: arena.gold },
  gang: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 64, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  on: { borderColor: arena.tealHi, backgroundColor: arena.panelHi },
  watch: { padding: 12, gap: 10 }, codeInput: { letterSpacing: 6, textAlign: "center" }, watchBtn: { width: 110 },
  past: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  result: { minWidth: 50, height: 30, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  resultWon: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});

export default withRapid(CupHub);

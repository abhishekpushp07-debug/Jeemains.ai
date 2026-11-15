import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Modal, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate, useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { EntryShow, effectOf } from "@/src/components/Entry";
import { BADGE_ICON } from "@/src/components/game";
import { arena } from "@/src/theme";
import { ARENA } from "@/src/arenaMode";
import { Emblem } from "@/src/rapid/Art";
import { GoldTitle, Panel, RaisedButton, SectionTitle } from "@/src/rapid/arena";
import { HeadToHeadCard } from "@/src/rapid/HeadToHead";
import { CupShowcase } from "@/src/rapid/CupShowcase";
import { CheerSquad } from "@/src/rapid/CheerSquad";
import { CrownShare } from "@/src/rapid/CrownShare";
import { prefetchSquad } from "@/src/rapid/squadArt";
import { Crown, GemStrip, InnerScreen, Note, WingedFace } from "@/src/rapid/parts";
import { ErrorBox, Sheet, withRapid } from "@/src/rapid/ui";
import { day, go, prettyCode, seenText, setArenaTab, shareFriendCode, shortSubject, useGangs } from "@/src/rapid/social";

function Tile({ label, value, testID }: { label: string; value: string | number; testID: string }) {
  return <View testID={testID} style={styles.tile}><T w="heavy" size={20} color={arena.gold}>{value}</T><T w="bold" size={10} color={arena.muted} style={styles.center}>{label}</T></View>;
}

/** A player's showcase: who they are, how they play, their diamonds and trophies, and the buttons to challenge them or bring them into a gang. Friends are made with a Friend Code. */
function Player() {
  const { pid, cheer } = useLocalSearchParams<{ pid: string; cheer?: string }>();
  const router = useRouter(), uid = useAuth().user?.id || "";
  const [cheering, setCheering] = useState(cheer === "1"); // from Cheer on the Champions Wall: the squad dances as you arrive
  const [sharing, setSharing] = useState(false);
  const q = useCached<any>(uid && pid ? `u.${uid}.rfplayer.${pid}` : null, () => rf(`/players/${pid}`, uid), false);
  const gangs = useGangs(uid);
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [note, setNote] = useState("");
  const [show, setShow] = useState(false), [pick, setPick] = useState(false), [more, setMore] = useState(false);
  const reload = q.reload;
  useFocusEffect(useCallback(() => { reload(); }, [reload]));
  const p = q.data, rel = p?.relation, s = p?.stats;
  useEffect(() => { prefetchSquad(p?.squad?.level); }, [p?.squad?.level]); // the squad's poses are ready before Cheer is tapped
  // The wings are 2.5 portraits wide; shrink the portrait on narrow phones so they stay inside the card.
  const portrait = Math.min(104, (Math.min(useWindowDimensions().width, 560) - 80) / 2.5);

  const act = async (key: string, run: () => Promise<any>) => {
    setBusy(key); setError(""); setNote("");
    try { await run(); invalidate(`u.${uid}.rffriends`); q.reload(); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };
  const addToGang = (gid: string, name: string) => act("gang" + gid, async () => {
    const r = await rf<any>(`/gangs/${gid}/members`, uid, { method: "POST", body: { pids: [pid] } });
    setPick(false); invalidate(`u.${uid}.rfgangs`);
    setNote(r.added ? `${p.name} is now in ${name}.` : r.skipped[0] || `${p.name} is already in ${name}.`);
  });
  const arenaTab = (tab: "store" | "gang", part = "") => { setArenaTab(tab, part); router.navigate("/(tabs)/rapid"); };

  return <InnerScreen testID="player-screen" title={p?.is_me ? "Your profile" : "Player"} sub={p?.title}>
    {!p ? (q.error ? <ErrorBox testID="player-error" error={q.error} retry={q.reload} /> : <ActivityIndicator testID="player-loading" color={arena.aqua} size="large" />) : <>
      <Panel gold testID="player-card" style={styles.card}>
        <WingedFace p={p} diamonds={p.diamonds} size={portrait} testID="player-wings" />
        <View style={styles.nameRow}>
          <GoldTitle size={26} center testID="player-name">{p.name}</GoldTitle>
          <Crown c={p.crown} size="lg" testID="player-crown" />
        </View>
        <T testID="player-title" w="heavy" size={13} color={arena.aqua}>{p.title} · Level {p.level}</T>
        <T testID="player-seen" w="bold" size={12} color={p.online ? arena.online : arena.muted}>{seenText(p)}</T>
      </Panel>

      {p.is_me ? <>
        <View style={styles.row}>
          <RaisedButton testID="player-change-avatar" label="Avatar & frame" onPress={() => arenaTab("store", "avatar")} style={styles.flex} />
          <RaisedButton testID="player-change-entry" label="Entry effect" onPress={() => arenaTab("store", "entry")} style={styles.flex} />
        </View>
        <RaisedButton testID="player-share-code" tone="wine" glyph="whatsapp" height={58} label="Send my Friend Code" sub={`${prettyCode(p.friend_code)} · ${p.friend_count} friend${p.friend_count === 1 ? "" : "s"} so far`} onPress={() => shareFriendCode(p.friend_code)} />
      </> : rel?.blocked ? <RaisedButton testID="player-unblock" tone="wine" label="Unblock" busy={busy === "unblock"} onPress={() => act("unblock", () => rf(`/blocks/${pid}`, uid, { method: "DELETE" }))} /> : <>
        <View style={styles.row}>
          {rel?.friend ? <View testID="player-friends-badge" style={styles.friends}><T w="heavy" size={14} color={arena.gold}>Friends ✓</T></View>
            : <RaisedButton testID="player-add-friend" label="Enter code" icon="friends" onPress={() => arenaTab("gang")} style={styles.flex} />}
          <RaisedButton testID="player-challenge" label="Challenge" icon="swords" disabled={!rel?.friend} onPress={() => router.push(go.challenge({ pid }))} style={styles.flex} />
        </View>
        {rel?.friend ? <RaisedButton testID="player-add-to-gang" tone="wine" label="Add to gang" onPress={() => setPick(true)} /> : <Note testID="player-code-note">Friends are made with a Friend Code. Ask {p.name} for theirs, enter it, and you can challenge each other.</Note>}
      </>}
      {note ? <T testID="player-note" w="bold" size={13} color={arena.aqua} style={styles.center}>{note}</T> : null}
      <ErrorBox testID="player-action-error" error={error} />

      {p.cups ? <CupShowcase cups={p.cups} name={p.name} me={p.is_me} squad={p.squad} onCheer={() => setCheering(true)} onShare={() => setSharing(true)} /> : null}

      <View style={styles.tiles}>
        <Tile testID="player-stat-matches" label="MATCHES" value={s.matches} />
        <Tile testID="player-stat-wins" label="WINS" value={s.wins} />
        <Tile testID="player-stat-winrate" label="WIN %" value={`${s.win_rate}%`} />
        <Tile testID="player-stat-streak" label="BEST WIN RUN" value={s.best_streak} />
        <Tile testID="player-stat-accuracy" label="ACCURACY" value={s.accuracy == null ? "—" : `${s.accuracy}%`} />
      </View>
      {p.head_to_head ? <HeadToHeadCard uid={uid} pid={p.pid} name={p.name} h2h={p.head_to_head} /> : null}

      <SectionTitle title="Diamond Vault" />
      <Panel gold testID="player-vault" style={styles.vault}>
        <GemStrip diamonds={p.diamonds} size={42} labels />
        <T w="bold" size={12} color={arena.aqua} style={styles.center}>Longest Phoenix streak: {p.best_phoenix}</T>
      </Panel>

      <RaisedButton testID="player-watch-entry" tone="wine" glyph="play" label={`Watch entry · ${effectOf(p.entry).label}`} onPress={() => setShow(true)} />

      <SectionTitle title={`Trophies (${p.trophies.length})`} />
      {p.trophies.length ? <View style={styles.trophies}>{p.trophies.map((b: any) => <View key={b.id} testID={`player-trophy-${b.id}`} style={styles.trophy}>
        <View style={styles.trophyIcon}><Icon name={BADGE_ICON[b.id] || "medal"} size={22} color={arena.badgeInk} /></View>
        <T w="heavy" size={11} color={arena.gold} numberOfLines={1}>{b.title}</T>
      </View>)}</View> : <Note testID="player-trophies-empty">No trophies yet.</Note>}

      <SectionTitle title="Last matches" />
      {p.recent.map((m: any) => <View key={m.id} testID={`player-match-${m.id}`} style={styles.match}>
        <View style={[styles.result, m.won && styles.resultWon]}><T w="heavy" size={11} color={m.won ? arena.badgeInk : arena.text}>{m.won ? "WON" : m.tie ? "TIE" : "LOST"}</T></View>
        <View style={styles.flex}>
          <T w="heavy" size={13} color={arena.text} numberOfLines={1}>{m.players > 2 ? `${m.players} players` : `vs ${m.opp_name}`} · {m.score}{m.players > 2 ? "" : ` – ${m.opp_score}`}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{shortSubject(m.subject)} · {m.chapter || "Mixed"} · {day(m.finished_at)}</T>
        </View>
      </View>)}
      {!p.recent.length ? <Note testID="player-matches-empty">No matches yet.</Note> : null}

      {!p.is_me && !rel?.blocked ? <RaisedButton testID="player-more" tone="wine" label="Remove or block" onPress={() => setMore(true)} /> : null}
      {/* Browser arena: a shared computer needs a way to sign out (the app does this from Home → Account). */}
      {p.is_me && ARENA ? <RaisedButton testID="player-account" tone="wine" glyph="account" label="Account & sign out" onPress={() => router.push("/account")} /> : null}
    </>}

    <Sheet visible={pick} onClose={() => setPick(false)} testID="player-gang-sheet">
      <GoldTitle size={20}>Add to which gang?</GoldTitle>
      {(gangs.data?.items || []).map((g) => <RaisedButton key={g.id} testID={`player-gang-${g.id}`} tone="wine" height={56} busy={busy === "gang" + g.id} disabled={!!busy} onPress={() => addToGang(g.id, g.name)}>
        <Emblem id={g.emblem} size={36} /><T w="heavy" size={15} color={arena.text} numberOfLines={1}>{g.name} · {g.members}</T>
      </RaisedButton>)}
      {gangs.data && !gangs.data.items.length ? <Note>You have no gang yet.</Note> : null}
      <RaisedButton testID="player-gang-new" label="Start a new gang" onPress={() => { setPick(false); router.push("/rapid/gang/new" as any); }} />
      <ErrorBox testID="player-gang-error" error={error} />
    </Sheet>
    <Sheet visible={more} onClose={() => setMore(false)} testID="player-more-sheet">
      <GoldTitle size={20}>{p?.name}</GoldTitle>
      {rel?.friend ? <RaisedButton testID="player-remove" tone="wine" label="Remove friend" busy={busy === "remove"} disabled={!!busy} onPress={() => act("remove", () => rf(`/friends/${pid}`, uid, { method: "DELETE" })).then(() => setMore(false))} /> : null}
      <RaisedButton testID="player-block" tone="danger" label="Block" busy={busy === "block"} disabled={!!busy} onPress={() => act("block", () => rf("/blocks", uid, { method: "POST", body: { pid } })).then(() => setMore(false))} />
      <T size={12} color={arena.muted}>A blocked player cannot add you, find you, put you in a gang or challenge you.</T>
    </Sheet>
    <Modal visible={show} transparent animationType="fade" onRequestClose={() => setShow(false)} statusBarTranslucent>
      {show && p ? <EntryShow solo testID="player-entry-show" players={[{ name: p.name, you: p.is_me, avatar: p.avatar, frame: p.frame, entry: p.entry, level: p.level, wins: s.wins }]} onDone={() => setShow(false)} /> : null}
    </Modal>
    {p?.cups?.won ? <CheerSquad visible={cheering} name={p.name} avatar={p.avatar} frame={p.frame} crown={p.crown?.won ? p.crown : { won: p.cups.won, real: p.cups.real }}
      level={p.squad?.level} title={p.squad?.title} onClose={() => setCheering(false)} /> : null}
    {p?.is_me && p.cups?.won ? <Modal visible={sharing} transparent animationType="fade" onRequestClose={() => setSharing(false)} statusBarTranslucent>
      <View style={styles.shareLayer}><ScrollView contentContainerStyle={styles.shareScroll} showsVerticalScrollIndicator={false}>
        <CrownShare s={{ name: p.name, avatar: p.avatar, frame: p.frame, no: p.cups.won, crown: p.crown?.won ? p.crown : { won: p.cups.won, real: p.cups.real },
          label: p.cups.recent[0]?.label || "Knockout Cup", size: p.cups.recent[0]?.size || 4, cabinet: true }} onBack={() => setSharing(false)} />
      </ScrollView></View>
    </Modal> : null}
  </InnerScreen>;
}

const styles = StyleSheet.create({
  shareLayer: { flex: 1, backgroundColor: arena.bgDeep }, shareScroll: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 20, paddingVertical: 32 },
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, row: { flexDirection: "row", gap: 10 },
  card: { alignItems: "center", gap: 4, padding: 18 },
  nameRow: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, flexWrap: "wrap" },
  friends: { flex: 1, height: 57, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.gold },
  tiles: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  tile: { flexGrow: 1, flexBasis: "30%", minHeight: 66, alignItems: "center", justifyContent: "center", gap: 2, padding: 6, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  vault: { padding: 14, gap: 10 },
  trophies: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  trophy: { width: "31.5%", alignItems: "center", gap: 4, padding: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  trophyIcon: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  match: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 56, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  result: { minWidth: 50, height: 30, paddingHorizontal: 6, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  resultWon: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});

export default withRapid(Player);

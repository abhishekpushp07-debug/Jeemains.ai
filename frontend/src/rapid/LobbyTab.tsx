import React, { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { rf, uuid } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { T } from "@/src/components/ui";
import { WeakRevision } from "@/src/components/ArenaLearning";
import { rewardsReady, useGameProfile } from "@/src/components/game";
import { arena } from "@/src/theme";
import { Alive, Emblem, GameIcon, GameIconName, PhoenixDiamond, topGem } from "./Art";
import { Badge, GoldTitle, Panel, RaisedButton, Ribbon, SectionTitle } from "./arena";
import { Jelly, Twinkles } from "./juice";
import { Face, GemStrip } from "./parts";
import { LiveStrip } from "./LiveStrip";
import { BadlaStrip } from "./BadlaStrip";
import { CupNightBanner } from "./CupNight";
import { ScopeSheet, SubjectChips } from "./ScopeSheet";
import { MAX_PICKS, cardCount, encodePicks, scopeLabel, scopeSubjects, setScope, useScope } from "./scope";
import { ErrorBox, Sheet } from "./ui";
import { Friend, GangRow, go, seenText, sendChallenge, setArenaTab, useFriends, useGangs, useInbox } from "./social";

function Sticker({ icon, label, badge, onPress, testID, delay, narrow }: { icon: GameIconName; label: string; badge: number; onPress: () => void; testID: string; delay: number; narrow?: boolean }) {
  return <Jelly testID={testID} onPress={onPress} accessibilityLabel={badge ? `${label}, ${badge}` : label} style={[styles.sticker, narrow && styles.stickerNarrow]}>
    <Alive kind="wiggle" delay={delay}><GameIcon name={icon} size={narrow ? 48 : 56} /></Alive>
    {badge ? <Badge n={badge > 99 ? "99+" : badge} testID={`${testID}-badge`} style={styles.stickerBadge} /> : null}
    <T w="heavy" size={narrow ? 10 : 11} color={arena.aqua} numberOfLines={1}>{label}</T>
  </Jelly>;
}

function Tile({ icon, label, sub, badge, onPress, testID, delay, disabled, narrow }: { icon: GameIconName; label: string; sub: string; badge?: number; onPress: () => void; testID: string; delay: number; disabled?: boolean; narrow?: boolean }) {
  return <Jelly testID={testID} onPress={onPress} disabled={disabled} accessibilityLabel={`${label}. ${sub}`} style={styles.tile}>
    <LinearGradient colors={[arena.panelHi, arena.panel]} style={styles.tileFace}>
      <View pointerEvents="none" style={styles.tileGloss} />
      <Alive kind="hop" delay={delay}><GameIcon name={icon} size={narrow ? 52 : 60} /></Alive>
      <T w="heavy" size={narrow ? 11.5 : 13} color={arena.text} numberOfLines={narrow ? 2 : 1} style={styles.center}>{label}</T>
      <T testID={`${testID}-sub`} w="bold" size={10.5} color={arena.aqua} numberOfLines={1}>{sub}</T>
    </LinearGradient>
    {badge ? <Badge n={badge} testID={`${testID}-badge`} style={styles.tileBadge} /> : null}
  </Jelly>;
}

/** Arena tab: a game lobby with a stage, three mode tiles, your gang and friends, and one big PLAY button. */
export function LobbyTab() {
  const router = useRouter(), { user } = useAuth(), uid = user?.id || "";
  const { width } = useWindowDimensions(), narrow = width < 360;
  const picks = useScope(), inbox = useInbox();
  const [sheet, setSheet] = useState<"" | "chapters" | "weak">("");
  const [quick, setQuick] = useState<{ gang?: GangRow; friend?: Friend } | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const prof = useGameProfile(uid), friends = useFriends(uid), gangs = useGangs(uid);
  const weak = useCached<any>(uid ? `u.${uid}.revision.JEE` : null, () => rf("/revision?exam=JEE", uid), false);
  const refresh = [prof.revalidate, friends.reload, gangs.reload, weak.reload];
  useFocusEffect(useCallback(() => { refresh.forEach((f) => f()); }, refresh)); // eslint-disable-line react-hooks/exhaustive-deps

  const available = cardCount(picks, cat.data?.subjects);
  const can = available >= 30 && !!uid;
  const play = (mode: "random" | "ai" | "solo") => router.push(mode === "solo" ? { pathname: "/rapid/session", params: { exam: "JEE", picks: encodePicks(picks), r: uuid() } } : go.duel({ mode, exam: "JEE", picks: encodePicks(picks), r: uuid() }));
  const challenge = async (body: { pids?: string[]; gang_id?: string }) => {
    setBusy(true); setError("");
    try { const room = await sendChallenge(uid, { ...body, picks }); setQuick(null); router.push(go.room(room)); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const ready = rewardsReady(prof.data);
  const weakCards = (weak.data?.items || []).reduce((n: number, row: any) => n + (row.remaining || 0), 0);
  const online = (friends.data?.items || []).filter((f) => f.online).length;
  const label = scopeLabel(picks);
  const cupLive = !!inbox?.cup, cupInvites = inbox?.cups?.length || 0;

  return <View style={styles.flex}>
    <ScrollView testID="rapid-fire-home" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={prof.refreshing} tintColor={arena.aqua} onRefresh={() => { prof.reload(); cat.reload(); friends.reload(); gangs.reload(); weak.reload(); }} />}>
      <View style={styles.stage}>
        <GoldTitle size={36} center testID="rf-title">RAPID FIRE</GoldTitle>
        <T testID="rf-tagline" w="heavy" size={14} color={arena.aqua} style={styles.tagline}>Pen down Fight</T>
        <View style={styles.diamondRow}>
          <Sticker testID="rf-daily-quests" icon="chest" label="Quests" badge={ready} delay={600} narrow={narrow} onPress={() => setArenaTab("trophy", "rewards")} />
          <View>
            <PhoenixDiamond width={Math.min(width * 0.52, 240, width - 32 - (narrow ? 136 : 152) - 4)} color={topGem(prof.data?.diamonds)} breathe testID="rf-phoenix" />
            <Twinkles spots={[[14, 18, 16], [86, 24, 13], [50, 6, 11], [24, 78, 10], [80, 74, 12]]} />
          </View>
          <Sticker testID="rf-weak-cards" icon="target" label="Weak cards" badge={weakCards} delay={1900} narrow={narrow} onPress={() => setSheet("weak")} />
        </View>
        <Ribbon testID="rf-chapter-picker" label={label} sub={cat.loading && !cat.data ? "Loading your cards…" : `${scopeSubjects(picks)} · ${picks.length}/${MAX_PICKS} · ${available} cards`} onPress={() => setSheet("chapters")} />
        <View style={styles.chipRow}><SubjectChips picks={picks} onChange={setScope} onLimit={() => setSheet("chapters")} /></View>
      </View>
      <ErrorBox testID="rf-catalog-error" error={cat.error || prof.error} retry={() => { cat.reload(); prof.reload(); }} />

      <View style={styles.tiles}>
        <Tile testID="rf-play-friends" icon="friends" label="Play Friends" sub={online ? `${online} online` : "Gang or friends"} badge={online} delay={300} narrow={narrow} onPress={() => router.push(go.challenge())} />
        <Tile testID="rf-duel-ai" icon="rival" label="Practice Rival" sub="No waiting" delay={1300} narrow={narrow} disabled={!can} onPress={() => play("ai")} />
        <Tile testID="rf-start-button" icon="bolt" label="Solo Sprint" sub="30 cards · 15 s" delay={2300} narrow={narrow} disabled={!can} onPress={() => play("solo")} />
      </View>

      <CupNightBanner uid={uid} />
      <Jelly testID="rf-knockout" accessibilityLabel={`Knockout Cup. 4, 8 or 16 players${cupLive ? ". Your cup is on" : ""}`} onPress={() => router.push(cupLive ? go.cup(inbox!.cup!) : go.cups())} style={styles.cupWrap}>
        <LinearGradient colors={["#5A0A14", arena.panel]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.cup}>
          <View pointerEvents="none" style={styles.tileGloss} />
          <Alive kind="breathe"><GameIcon name="trophy" size={narrow ? 48 : 64} /></Alive>
          <View style={styles.flex}>
            <T w="heavy" size={narrow ? 10 : 11} color={arena.aqua} style={styles.kicker} numberOfLines={1}>{cupLive ? "YOUR CUP IS ON" : narrow ? "NEW" : "NEW · KNOCKOUT CUP"}</T>
            <GoldTitle size={narrow ? 18 : 22}>Knockout Cup</GoldTitle>
            <T w="bold" size={narrow ? 10.5 : 11.5} color={arena.muted} numberOfLines={1}>{narrow ? "4 · 8 · 16 players" : "4 · 8 · 16 players · live bracket"}</T>
          </View>
          <View style={[styles.cupGo, narrow && styles.cupGoNarrow]}><T w="heavy" size={13} color={arena.text}>{cupLive ? "OPEN" : "PLAY"}</T></View>
        </LinearGradient>
        {cupInvites ? <Badge n={cupInvites} testID="rf-knockout-badge" style={styles.tileBadge} /> : null}
      </Jelly>

      <LiveStrip uid={uid} />
      <BadlaStrip uid={uid} />

      <SectionTitle title="Your gang & friends" action="See all" testID="rf-open-gang-tab" onAction={() => setArenaTab("gang")} />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.people} testID="rf-people-strip">
        <Jelly testID="rf-people-add" accessibilityLabel="Add a friend or start a gang" onPress={() => setArenaTab("gang")} style={styles.person}>
          <View style={styles.add}><T w="heavy" size={28} color={arena.text}>+</T></View>
          <T w="heavy" size={11} color={arena.aqua} numberOfLines={1}>Add</T>
        </Jelly>
        {(gangs.data?.items || []).map((g) => <Jelly key={g.id} testID={`rf-people-gang-${g.id}`} accessibilityLabel={`${g.name} gang, ${g.online} online`} onPress={() => { setError(""); setQuick({ gang: g }); }} style={styles.person}>
          <Emblem id={g.emblem} size={52} />
          <T w="heavy" size={11} color={arena.text} numberOfLines={1}>{g.name}</T>
          <T w="bold" size={10} color={g.online ? arena.online : arena.faint}>{g.online} online</T>
        </Jelly>)}
        {(friends.data?.items || []).map((f) => <Jelly key={f.pid} testID={`rf-people-friend-${f.pid}`} accessibilityLabel={`${f.name}, ${seenText(f)}`} onPress={() => { setError(""); setQuick({ friend: f }); }} style={styles.person}>
          <Face p={f} size={52} />
          <T w="heavy" size={11} color={arena.text} numberOfLines={1}>{f.name}</T>
          <T w="bold" size={10} color={arena.faint}>Lv {f.level}</T>
        </Jelly>)}
        {friends.data && !friends.data.items.length && !gangs.data?.items.length ? <T testID="rf-people-empty" size={12} color={arena.muted} style={styles.peopleEmpty}>No friends yet. Tap + and bring your gang in!</T> : null}
      </ScrollView>

      <Jelly testID="rf-vault-strip" accessibilityLabel="Diamond Vault" onPress={() => router.push("/rapid/vault" as any)}>
        <Panel flat style={styles.vault}>
          <T w="heavy" size={12} color={arena.gold} style={styles.vaultTitle}>DIAMOND VAULT</T>
          <GemStrip diamonds={prof.data?.diamonds} size={38} />
        </Panel>
      </Jelly>
      <T testID="rf-practice-note" size={10} color={arena.faint} style={styles.center}>Practice, not exam marks. Coins and diamonds are earned only by playing.</T>
    </ScrollView>

    <View style={styles.dock}>
      <RaisedButton testID="rf-duel-random" label="PLAY" sub={`Quick Match · ${label}`} icon="swords" height={64} streak disabled={!can} onPress={() => play("random")} />
    </View>

    <ScopeSheet visible={sheet === "chapters"} onClose={() => setSheet("")} subjects={cat.data?.subjects || []} value={picks} onDone={setScope} />
    <Sheet visible={sheet === "weak"} onClose={() => setSheet("")} testID="rf-weak-sheet">{uid ? <WeakRevision uid={uid} exam="JEE" /> : null}</Sheet>
    <Sheet visible={!!quick} onClose={() => setQuick(null)} testID="rf-quick-sheet">
      {quick?.gang ? <View style={styles.quick}>
        <Emblem id={quick.gang.emblem} size={92} />
        <GoldTitle size={24} center>{quick.gang.name}</GoldTitle>
        <T w="bold" size={13} color={arena.aqua}>{quick.gang.members} members · {quick.gang.online} online</T>
        <RaisedButton testID="rf-quick-challenge-gang" label="CHALLENGE GANG" sub={label} icon="swords" height={60} busy={busy} disabled={quick.gang.members < 2} onPress={() => challenge({ gang_id: quick.gang!.id })} style={styles.stretch} />
        <RaisedButton testID="rf-quick-open-gang" label="Open gang" tone="wine" onPress={() => { const g = quick.gang!; setQuick(null); router.push(go.gang(g.id)); }} style={styles.stretch} />
      </View> : quick?.friend ? <View style={styles.quick}>
        <Face p={quick.friend} size={92} />
        <GoldTitle size={24} center>{quick.friend.name}</GoldTitle>
        <T w="bold" size={13} color={quick.friend.online ? arena.online : arena.muted}>Level {quick.friend.level} · {seenText(quick.friend)}</T>
        <RaisedButton testID="rf-quick-challenge-friend" label="CHALLENGE" sub={label} icon="swords" height={60} busy={busy} onPress={() => challenge({ pids: [quick.friend!.pid] })} style={styles.stretch} />
        <RaisedButton testID="rf-quick-open-profile" label="View profile" tone="wine" onPress={() => { const f = quick.friend!; setQuick(null); router.push(go.player(f.pid)); }} style={styles.stretch} />
      </View> : null}
      <ErrorBox testID="rf-quick-error" error={error} />
    </Sheet>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 }, center: { textAlign: "center" }, stretch: { alignSelf: "stretch" },
  content: { paddingHorizontal: 16, paddingTop: 6, paddingBottom: 18, gap: 14 },
  stage: { alignItems: "center", gap: 2 }, tagline: { letterSpacing: 3, textTransform: "uppercase" }, chipRow: { alignSelf: "stretch", marginTop: 8 }, kicker: { letterSpacing: 1.5 },
  cupWrap: { borderRadius: 22, backgroundColor: arena.goldDeep, paddingBottom: 5 },
  cup: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 92, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 22, borderWidth: 1.5, borderColor: arena.gold, overflow: "hidden" },
  cupGo: { height: 44, paddingHorizontal: 14, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  cupGoNarrow: { paddingHorizontal: 10 }, stickerNarrow: { width: 68 },
  diamondRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", alignSelf: "stretch", marginVertical: 2 },
  sticker: { width: 76, minHeight: 84, alignItems: "center", justifyContent: "center", gap: 2 }, stickerBadge: { position: "absolute", top: 2, right: 6 },
  tiles: { flexDirection: "row", gap: 10 },
  tile: { flex: 1, borderRadius: 20, backgroundColor: arena.panelEdge, paddingBottom: 6 },
  tileFace: { borderRadius: 20, borderWidth: 1.5, borderColor: arena.rim, alignItems: "center", paddingTop: 10, paddingBottom: 10, paddingHorizontal: 4, gap: 1, overflow: "hidden" },
  tileGloss: { position: "absolute", top: 2, left: 3, right: 3, height: "38%", borderRadius: 18, backgroundColor: arena.goldSoft },
  tileBadge: { position: "absolute", top: -6, right: -4 },
  people: { gap: 6, paddingRight: 8, alignItems: "flex-start" }, person: { width: 76, alignItems: "center", gap: 2, minHeight: 84 }, peopleEmpty: { alignSelf: "center", maxWidth: 220, marginLeft: 6 },
  add: { width: 52, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 2, borderColor: arena.tealOutline, borderBottomWidth: 5, borderBottomColor: arena.tealDeep },
  vault: { padding: 12, gap: 8 }, vaultTitle: { letterSpacing: 2, textAlign: "center" },
  // Room below PLAY for the Phoenix Diamond rising out of the arena bar.
  dock: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 24 },
  quick: { alignItems: "center", gap: 10 },
});

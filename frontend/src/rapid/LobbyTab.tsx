import React, { useCallback, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { rf, uuid } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { rewardsReady, useGameProfile } from "@/src/components/game";
import { arena } from "@/src/theme";
import { Alive, Emblem, GameIcon, GameIconName, PhoenixDiamond, topGem } from "./Art";
import { Badge, GoldTitle, Panel, RaisedButton, Ribbon, SectionTitle } from "./arena";
import { Jelly, Twinkles } from "./juice";
import { Face, GemStrip } from "./parts";
import { LiveStrip } from "./LiveStrip";
import { BadlaStrip } from "./BadlaStrip";
import { CupNightBanner } from "./CupNight";
import { ChampionsWall } from "./ChampionsWall";
import { ScopeSheet } from "./ScopeSheet";
import { CARD_SECONDS, Pick, cardCount, encodePicks, fitCount, getCardCount, scopeLabel, setScope, useCardCount, useScope } from "./scope";
import { ErrorBox, Sheet } from "./ui";
import { Friend, GangRow, go, seenText, sendChallenge, setArenaTab, useFriends, useGangs, useInbox } from "./social";
import { Glitter } from "./Glitter";
import { AllIndiaCard } from "./AllIndiaCard";
import { dailyStyleName, useDaily, useDailyLook } from "./daily";
import { WeakSprintStrip, useWeakTopics } from "./WeakSprint";
import { WeakChapters, WeakSheet } from "./WeakSheet";
import { useArenaFrameWatch } from "@/src/motion";

const NONE: Pick[] = [];

function Sticker({ icon, label, badge, onPress, testID, delay, narrow }: { icon: GameIconName; label: string; badge: number; onPress: () => void; testID: string; delay: number; narrow?: boolean }) {
  return <Jelly testID={testID} onPress={onPress} accessibilityLabel={badge ? `${label}, ${badge}` : label} style={[styles.sticker, narrow && styles.stickerNarrow]}>
    <Alive kind="wiggle" delay={delay}><GameIcon name={icon} size={narrow ? 48 : 56} /></Alive>
    {badge ? <Badge n={badge > 99 ? "99+" : badge} testID={`${testID}-badge`} style={styles.stickerBadge} /> : null}
    <T w="heavy" size={narrow ? 10 : 11} color={arena.aqua} numberOfLines={1}>{label}</T>
  </Jelly>;
}

function Tile({ icon, label, sub, badge, onPress, testID, delay, disabled, narrow }: { icon: GameIconName; label: string; sub: string; badge?: number; onPress: () => void; testID: string; delay: number; disabled?: boolean; narrow?: boolean }) {
  return <Jelly testID={testID} onPress={onPress} disabled={disabled} accessibilityLabel={`${label}. ${sub}`} style={styles.tile}>
    <Glitter radius={20} sparkles={2} inner={styles.tileInner}><LinearGradient colors={[arena.panelHi, arena.panel]} style={styles.tileFace}>
      <View pointerEvents="none" style={styles.tileGloss} />
      <Alive kind="hop" delay={delay}><GameIcon name={icon} size={narrow ? 52 : 60} /></Alive>
      <T w="heavy" size={narrow ? 11.5 : 13} color={arena.text} numberOfLines={narrow ? 2 : 1} style={styles.center}>{label}</T>
      <T testID={`${testID}-sub`} w="bold" size={10.5} color={arena.aqua} numberOfLines={1}>{sub}</T>
    </LinearGradient></Glitter>
    {badge ? <Badge n={badge} testID={`${testID}-badge`} style={styles.tileBadge} /> : null}
  </Jelly>;
}

/** Arena tab: a game lobby with a stage, three mode tiles, your gang and friends, and one big PLAY button. */
export function LobbyTab() {
  const router = useRouter(), { user } = useAuth(), uid = user?.id || "";
  useArenaFrameWatch();
  const { width } = useWindowDimensions(), narrow = width < 360;
  const picks = useScope(), inbox = useInbox();
  const [sheet, setSheet] = useState<"" | "chapters" | "weak">(""), [pending, setPending] = useState<"" | "ai" | "solo">("");
  const [quick, setQuick] = useState<{ gang?: GangRow; friend?: Friend } | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const cat = useCached<any>("rf.catalog.JEE.portrait", () => rf("/catalog?exam=JEE", uid));
  const prof = useGameProfile(uid), friends = useFriends(uid), gangs = useGangs(uid);
  const weak = useCached<WeakChapters>(uid ? `u.${uid}.revision.JEE` : null, () => rf("/revision?exam=JEE", uid), false);
  const daily = useDaily(uid), look = useDailyLook(), cardSize = Math.min(width, 560) - 32, weakTopics = useWeakTopics(uid);
  const { revalidate } = prof, { reload: reloadFriends } = friends, { reload: reloadGangs } = gangs, { reload: reloadWeak } = weak, { reload: reloadDaily } = daily, { reload: reloadTopics } = weakTopics;
  useFocusEffect(useCallback(() => { revalidate(); reloadFriends(); reloadGangs(); reloadWeak(); reloadDaily(); reloadTopics(); }, [revalidate, reloadFriends, reloadGangs, reloadWeak, reloadDaily, reloadTopics]));

  const available = cardCount(picks, cat.data?.subjects);
  const chosen = useCardCount(), size = cat.data ? fitCount(chosen, available) : 0;
  const can = !!uid;
  const play = (mode: "random" | "ai" | "solo", on: Pick[] = picks) => {
    const p = encodePicks(on), n = String(fitCount(getCardCount(), cardCount(on, cat.data?.subjects)));
    router.push(mode === "solo" ? { pathname: "/rapid/session", params: { exam: "JEE", picks: p, n, r: uuid() } } : go.duel({ mode, exam: "JEE", picks: p, n, r: uuid() }));
  };
  // Nothing is ever picked for the student: a mode tile always opens the picker, with every chapter unticked, and the round starts from there.
  const start = (mode: "ai" | "solo") => { setPending(mode); setSheet("chapters"); };
  // Quick Match starts from the Subjects sheet, right where the subject or chapter is chosen.
  const quickMatch = (next: Pick[]) => play("random", next);
  const challenge = async (body: { pids?: string[]; gang_id?: string }) => {
    setBusy(true); setError("");
    try { const room = await sendChallenge(uid, { ...body, picks, count: size || 30 }); setQuick(null); router.push(go.room(room)); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  const ready = rewardsReady(prof.data);
  const weakCards = (weak.data?.items || []).reduce((n, row) => n + (row.remaining || 0), 0);
  const online = (friends.data?.items || []).filter((f) => f.online).length;
  const label = scopeLabel(picks);
  const cupLive = !!inbox?.cup, cupInvites = inbox?.cups?.length || 0;

  return <View style={styles.flex}>
    <ScrollView testID="rapid-fire-home" showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={prof.refreshing} tintColor={arena.aqua} onRefresh={() => { prof.reload(); cat.reload(); friends.reload(); gangs.reload(); weak.reload(); daily.reload(); weakTopics.reload(); }} />}>
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
        {/* Quick Play: a teal key like the first PLAY button. Subjects, chapters and the 30/50/100 cards are chosen on the next screen, and PLAY starts there. */}
        <Ribbon testID="rf-chapter-picker" label="Quick Play" tone="teal" onPress={() => setSheet("chapters")} />
      </View>
      <ErrorBox testID="rf-catalog-error" error={cat.error || prof.error} retry={() => { cat.reload(); prof.reload(); }} />

      <View style={styles.tiles}>
        <Tile testID="rf-play-friends" icon="friends" label="Play Friends" sub={online ? `${online} online` : "Gang or friends"} badge={online} delay={300} narrow={narrow} onPress={() => router.push(go.challenge())} />
        <Tile testID="rf-duel-ai" icon="rival" label="Practice Rival" sub="No waiting" delay={1300} narrow={narrow} disabled={!can} onPress={() => start("ai")} />
        <Tile testID="rf-start-button" icon="bolt" label="Solo Sprint" sub={`${chosen} cards · ${CARD_SECONDS} s`} delay={2300} narrow={narrow} disabled={!can} onPress={() => start("solo")} />
      </View>

      {/* All India Rapid: the big square right below the three mode tiles. The whole card opens today’s 45 PCM cards. */}
      <View style={styles.daily}>
        <AllIndiaCard d={daily.data} look={look} size={cardSize} sound onPress={() => router.push(go.daily())} onLongPress={() => router.push(go.dailyStyles())} />
        <Jelly testID="rf-all-india-style" accessibilityLabel={`Card style ${dailyStyleName(look)}. Change style`} onPress={() => router.push(go.dailyStyles())} style={styles.stylePill}>
          <Icon name="palette" size={14} color={arena.gold} />
          <T w="heavy" size={11.5} color={arena.text}>{dailyStyleName(look)}</T>
          <T w="bold" size={11.5} color={arena.aqua}>· Change style ›</T>
        </Jelly>
      </View>

      <WeakSprintStrip uid={uid} narrow={narrow} />
      <CupNightBanner uid={uid} />
      <ChampionsWall uid={uid} />
      <Jelly testID="rf-knockout" accessibilityLabel={`Knockout Cup. 4, 8 or 16 players${cupLive ? ". Your cup is on" : ""}`} onPress={() => router.push(cupLive ? go.cup(inbox!.cup!) : go.cups())}>
        <Glitter radius={22} inner={styles.cupInner}><LinearGradient colors={["#5A0A14", arena.panel]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.cup}>
          <View pointerEvents="none" style={styles.tileGloss} />
          <Alive kind="breathe"><GameIcon name="trophy" size={narrow ? 48 : 64} /></Alive>
          <View style={styles.flex}>
            <T w="heavy" size={narrow ? 10 : 11} color={arena.aqua} style={styles.kicker} numberOfLines={1}>{cupLive ? "YOUR CUP IS ON" : narrow ? "NEW" : "NEW · KNOCKOUT CUP"}</T>
            <GoldTitle size={narrow ? 18 : 22}>Knockout Cup</GoldTitle>
            <T w="bold" size={narrow ? 10.5 : 11.5} color={arena.muted} numberOfLines={1}>{narrow ? "4 · 8 · 16 players" : "4 · 8 · 16 players · live bracket"}</T>
          </View>
          <View style={[styles.cupGo, narrow && styles.cupGoNarrow]}><T w="heavy" size={13} color={arena.text}>{cupLive ? "OPEN" : "PLAY"}</T></View>
        </LinearGradient></Glitter>
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

    {/* The picker always opens with nothing ticked (`NONE`); what the student then picks is kept as the lobby's choice for Play Friends, cups and gang wars. */}
    <ScopeSheet visible={sheet === "chapters"} onClose={() => { setSheet(""); setPending(""); }} subjects={cat.data?.subjects || []} value={NONE}
      onDone={(next) => { setScope(next); if (pending) play(pending, next); }} onPlay={uid && !pending ? quickMatch : undefined}
      action={pending === "solo" ? "START SOLO SPRINT" : pending === "ai" ? "PLAY PRACTICE RIVAL" : undefined} hint={pending ? "Pick your subjects or chapters first" : undefined} />
    <WeakSheet visible={sheet === "weak"} onClose={() => setSheet("")} chapters={weak} topics={weakTopics} />
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
  // Room at the bottom for the Phoenix Diamond rising out of the arena bar.
  content: { paddingHorizontal: 16, paddingTop: 6, paddingBottom: 36, gap: 14 },
  stage: { alignItems: "center", gap: 2 }, tagline: { letterSpacing: 3, textTransform: "uppercase" }, kicker: { letterSpacing: 1.5 },
  cupInner: { borderBottomWidth: 4, borderBottomColor: arena.goldDeep },
  cup: { flexDirection: "row", alignItems: "center", gap: 12, minHeight: 92, paddingHorizontal: 14, paddingVertical: 10, overflow: "hidden" },
  cupGo: { height: 44, paddingHorizontal: 14, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  cupGoNarrow: { paddingHorizontal: 10 }, stickerNarrow: { width: 68 },
  diamondRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", alignSelf: "stretch", marginVertical: 2 },
  sticker: { width: 76, minHeight: 84, alignItems: "center", justifyContent: "center", gap: 2 }, stickerBadge: { position: "absolute", top: 2, right: 6 },
  tiles: { flexDirection: "row", gap: 10 },
  tile: { flex: 1 }, tileInner: { borderBottomWidth: 5, borderBottomColor: arena.panelEdge },
  tileFace: { flexGrow: 1, alignItems: "center", paddingTop: 10, paddingBottom: 10, paddingHorizontal: 4, gap: 1, overflow: "hidden" },
  tileGloss: { position: "absolute", top: 2, left: 3, right: 3, height: "38%", borderRadius: 18, backgroundColor: arena.goldSoft },
  tileBadge: { position: "absolute", top: -6, right: -4 },
  people: { gap: 6, paddingRight: 8, alignItems: "flex-start" }, person: { width: 76, alignItems: "center", gap: 2, minHeight: 84 }, peopleEmpty: { alignSelf: "center", maxWidth: 220, marginLeft: 6 },
  add: { width: 52, height: 52, borderRadius: 26, alignItems: "center", justifyContent: "center", backgroundColor: arena.teal, borderWidth: 2, borderColor: arena.tealOutline, borderBottomWidth: 5, borderBottomColor: arena.tealDeep },
  vault: { padding: 12, gap: 8 }, vaultTitle: { letterSpacing: 2, textAlign: "center" },
  quick: { alignItems: "center", gap: 10 },
  daily: { gap: 8 },
  stylePill: { flexDirection: "row", alignItems: "center", alignSelf: "center", gap: 5, minHeight: 44, paddingHorizontal: 14, borderRadius: 18, backgroundColor: arena.scrim, borderWidth: 1, borderColor: arena.rim },
});

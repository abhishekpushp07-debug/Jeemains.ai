import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, BackHandler, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Clipboard from "expo-clipboard";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { Alive, GameIcon } from "@/src/rapid/Art";
import { ArenaBg, CloseButton, GoldTitle, Panel, RaisedButton, SectionTitle } from "@/src/rapid/arena";
import { Confetti, Jelly, LiveDot, Pop, Twinkles } from "@/src/rapid/juice";
import { Face, PersonRow } from "@/src/rapid/parts";
import { ErrorBox, Sheet, withRapid } from "@/src/rapid/ui";
import { clock, go, refreshInbox, sendWhatsApp } from "@/src/rapid/social";

type Seat = { pid?: string | null; name: string; avatar?: string | null; frame?: string | null; level?: number; bot: boolean; you: boolean; out: boolean };
type Match = { a: number | null; b: number | null; winner: number | null; score: number[] | null; duel_id: string | null; live: boolean; starts_in: number; mine: boolean };
const ROUND = (n: number) => (n === 1 ? "Final" : n === 2 ? "Semi-finals" : n === 4 ? "Quarter-finals" : n === 8 ? "Round of 16" : `Round of ${n * 2}`);
const SLOT = 92, CARD_W = 172;

/** One match in the bracket: both players with their scores, the winner in gold, LIVE with a Watch button while it is being played. */
function MatchCard({ m, seats, onWatch, testID }: { m?: Match; seats: Seat[]; onWatch: (did: string) => void; testID: string }) {
  const line = (i: number | null | undefined, k: 0 | 1) => {
    const p = i == null ? null : seats[i], won = m?.winner != null && m.winner === i, lost = m?.winner != null && i != null && m.winner !== i;
    return <View style={[styles.line, won && styles.lineWon, lost && styles.lineLost]}>
      {p ? <Avatar icon={p.avatar} frame={p.frame} size={24} /> : <View style={styles.ghost} />}
      <T w="heavy" size={12} color={won ? arena.badgeInk : p?.you ? arena.gold : p ? arena.text : arena.faint} numberOfLines={1} style={styles.flex}>{p ? (p.you ? "You" : p.name) : m ? "BYE" : "TBD"}</T>
      {m?.score && p ? <T w="heavy" size={13} color={won ? arena.badgeInk : arena.text}>{m.score[k]}</T> : null}
    </View>;
  };
  const watchable = !!m?.duel_id && m.winner == null && !m.mine;
  return <View testID={testID} style={[styles.match, m?.live && styles.matchLive, m?.mine && m.winner == null && styles.matchMine]}>
    {line(m?.a, 0)}{line(m?.b, 1)}
    {m?.duel_id && m.winner == null ? <View style={styles.matchFoot}>
      {m.live ? <><LiveDot size={8} /><T w="heavy" size={10} color={arena.danger}>LIVE</T></> : <T w="bold" size={10} color={arena.aqua}>{m.starts_in ? `Starts in ${m.starts_in}s` : "Starting…"}</T>}
      {watchable ? <Jelly testID={`${testID}-watch`} accessibilityLabel="Watch this match live" onPress={() => onWatch(m.duel_id!)} style={styles.watch}><Icon name="eye" size={13} color={arena.text} /><T w="heavy" size={10} color={arena.text}>Watch</T></Jelly>
        : m.mine ? <T w="heavy" size={10} color={arena.gold} style={styles.push}>YOUR MATCH</T> : null}
    </View> : null}
  </View>;
}

/** The whole bracket, round by round from left to right. Rounds not drawn yet show as TBD. It slides to the round being played. */
function Bracket({ cup, onWatch }: { cup: any; onWatch: (did: string) => void }) {
  const cols: number[] = [];
  for (let n = cup.size / 2; n >= 1; n /= 2) cols.push(n);
  const height = (cup.size / 2) * SLOT;
  const ref = useRef<React.ComponentRef<typeof ScrollView>>(null);
  // Slide so the round being played (or the Final, once the cup is over) is the first column on screen.
  const focus = cup.status === "finished" ? cols.length - 1 : Math.max(0, cup.round);
  useEffect(() => {
    const t = setTimeout(() => ref.current?.scrollTo({ x: focus * (CARD_W + 14), animated: true }), 350);
    return () => clearTimeout(t);
  }, [focus]);
  return <ScrollView ref={ref} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.bracket} testID="cup-bracket">
    {cols.map((n, k) => {
      const rd = cup.rounds[k], current = cup.status === "live" && cup.round === k;
      return <View key={k} style={styles.col}>
        <View style={[styles.colHead, current && styles.colHeadOn]}><T w="heavy" size={11} color={current ? arena.badgeInk : arena.gold}>{(rd?.name || ROUND(n)).toUpperCase()}</T></View>
        <View style={[styles.colBody, { height }]}>
          {Array.from({ length: n }, (_, i) => <View key={i} style={styles.slot}>
            <MatchCard m={rd?.matches[i]} seats={cup.players} onWatch={onWatch} testID={`cup-match-${k}-${i}`} />
            {n > 1 ? <View style={[styles.link, i % 2 ? styles.linkUp : styles.linkDown]} /> : null}
          </View>)}
        </View>
      </View>;
    })}
    <View style={styles.col}>
      <View style={styles.colHead}><T w="heavy" size={11} color={arena.gold}>CHAMPION</T></View>
      <View style={[styles.colBody, { height }]}>
        <View style={styles.crown}>
          <GameIcon name="trophy" size={56} />
          {cup.champion != null ? <><Avatar icon={cup.players[cup.champion].avatar} frame={cup.players[cup.champion].frame} size={40} /><T w="heavy" size={12} color={arena.gold} numberOfLines={1}>{cup.players[cup.champion].you ? "You" : cup.players[cup.champion].name}</T></> : <T w="bold" size={11} color={arena.faint}>Who will it be?</T>}
        </View>
      </View>
    </View>
  </ScrollView>;
}

/** A knockout cup from the lobby to the champion: seats filling up, the live bracket with every match, and the trophy. */
function Cup() {
  const { cid } = useLocalSearchParams<{ cid: string }>();
  const router = useRouter(), insets = useSafeAreaInsets(), uid = useAuth().user?.id || "";
  const [cup, setCup] = useState<any>(null), [error, setError] = useState(""), [busy, setBusy] = useState(""), [copied, setCopied] = useState(false);
  const [, tick] = useState(0);
  const fetchedAt = useRef(0), focused = useRef(true), sent = useRef<string | null>(null);
  const load = useCallback(async () => {
    try { const c = await rf(`/cups/${cid}`, uid); fetchedAt.current = Date.now(); setCup(c); setError(""); }
    catch (e: any) { setError(e.message); }
  }, [cid, uid]);
  const status: string = cup?.status || "";
  const moving = !cup || status === "open" || status === "live";
  useEffect(() => {
    if (!uid || !moving) return;
    load();
    const poll = setInterval(load, 2000), second = setInterval(() => tick((n) => n + 1), 1000);
    return () => { clearInterval(poll); clearInterval(second); };
  }, [uid, moving, load]);
  useFocusEffect(useCallback(() => { focused.current = true; load(); return () => { focused.current = false; }; }, [load]));
  // Your next match is seated: go straight in, so the entry show starts with your rival's.
  useEffect(() => {
    if (cup?.my_duel && focused.current && sent.current !== cup.my_duel) { sent.current = cup.my_duel; router.push(go.duel({ did: cup.my_duel })); }
  }, [cup?.my_duel]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (status === "finished") ["rfprofile", "rfcups", "rfduels"].forEach((k) => invalidate(`u.${uid}.${k}`)); }, [status, uid]);

  const act = async (what: "join" | "leave" | "start") => {
    setBusy(what); setError("");
    try { const r = await rf<any>(`/cups/${cid}/${what}`, uid, { method: "POST", body: {} }); if (what === "leave") back(); else setCup(r); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(""); refreshInbox(uid); }
  };
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"));
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { back(); return true; });
    return () => sub.remove();
  }, [])); // eslint-disable-line react-hooks/exhaustive-deps

  const left = cup ? Math.max(0, Math.round(cup.expires_in - (Date.now() - fetchedAt.current) / 1000)) : 0;
  const me: Seat | undefined = cup?.players.find((p: Seat) => p.you);
  const champ: Seat | null = cup?.champion != null ? cup.players[cup.champion] : null;
  const share = () => sendWhatsApp(`🏆 Watch my Rapid Fire Knockout Cup live on JEECIRCLE.AI!\n${cup.size} players · ${cup.label}\nWatch code: ${cup.code}\nApp → Rapid Fire → Knockout Cup → Watch with a code.`);
  const remind = () => sendWhatsApp(`🏆 Join my Rapid Fire Knockout Cup on JEECIRCLE.AI!\n${cup.size} players · ${cup.label} · ${cup.cards} cards a match\nOpen the app → Rapid Fire → Knockout Cup and press Join before the timer runs out.`);
  const [confirm, setConfirm] = useState(false);
  const watch = (did: string) => router.push(go.watch(did));
  const roundName = cup?.rounds?.[cup.round]?.name;

  let body: React.ReactNode;
  if (!cup) body = <View style={styles.middle}>{error ? <><ErrorBox testID="cup-error" error={error} retry={load} /><RaisedButton testID="cup-back" tone="wine" label="Back" onPress={back} style={styles.stretch} /></> : <ActivityIndicator testID="cup-loading" color={arena.aqua} size="large" />}</View>;
  else if (status === "cancelled" || status === "expired") body = <View style={styles.middle} testID="cup-closed">
    <GameIcon name="trophy" size={92} />
    <GoldTitle size={26} center>{status === "expired" ? "Not enough players" : "Cup closed"}</GoldTitle>
    <T size={13} color={arena.muted} style={styles.center}>{status === "expired" ? "Nobody joined in time. Try an Open Cup: rivals are always ready." : "The host closed this cup."}</T>
    <RaisedButton testID="cup-new" icon="trophy" height={60} label="New cup" onPress={() => router.replace(go.cups())} style={styles.stretch} />
  </View>;
  else body = <ScrollView style={styles.flex} showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
    {status === "finished" && champ ? <Pop><Panel gold testID="cup-champion" style={styles.hero}>
      <View><Alive kind="breathe"><GameIcon name="trophy" size={112} /></Alive><Twinkles spots={[[6, 18, 16], [94, 24, 13], [50, 0, 12], [14, 88, 10], [88, 84, 12]]} /></View>
      <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>CHAMPION</T>
      <Face p={champ} size={72} />
      <GoldTitle size={30} center testID="cup-champion-name">{champ.you ? "YOU WON THE CUP!" : champ.name}</GoldTitle>
      <T w="bold" size={13} color={arena.text} style={styles.center}>{cup.prize ? `+${cup.prize} coins for you` : me ? (me.out ? "Knocked out this time. Next cup is yours!" : "") : "What a cup! Thanks for watching."}</T>
    </Panel></Pop> : status === "open" ? <Panel gold testID="cup-lobby" style={styles.hero}>
      <Alive kind="breathe"><GameIcon name="trophy" size={84} /></Alive>
      <T testID="cup-seats-count" w="heavy" size={12} color={arena.aqua} style={styles.spaced}>{cup.players.length} / {cup.size} SEATS</T>
      <View style={styles.fillTrack}><View style={[styles.fillBar, { width: `${(cup.players.length / cup.size) * 100}%` }]} /></View>
      <T testID="cup-countdown" w="heavy" size={44} color={left <= 10 ? arena.danger : arena.gold}>{clock(left)}</T>
      <T size={12} color={arena.muted} style={styles.center}>{cup.kind === "open" ? "Starts when all seats fill or the timer ends. Practice rivals take the empty seats." : "Starts when the host presses START, all seats fill, or the timer ends. Empty seats become byes."}</T>
    </Panel> : <Panel testID="cup-live" style={styles.live}>
      <LiveDot />
      <View style={styles.flex}>
        <T w="heavy" size={12} color={arena.aqua} style={styles.spaced}>{(roundName || "Round").toUpperCase()} · LIVE</T>
        <T w="heavy" size={15} color={arena.text}>{cup.my_duel ? "Your match is ready!" : me && !me.out ? "You’re through. Next round soon…" : me?.out ? "You’re out. Keep watching!" : "Follow every match live"}</T>
      </View>
      <GameIcon name="trophy" size={40} />
    </Panel>}

    {cup.my_duel ? <RaisedButton testID="cup-play" icon="swords" height={64} streak label="PLAY YOUR MATCH" sub={`${cup.cards} cards · winner goes through`} onPress={() => router.push(go.duel({ did: cup.my_duel }))} /> : null}

    {status === "open" ? <View style={styles.seats} testID="cup-seats">
      {Array.from({ length: cup.size }, (_, i) => {
        const p: Seat | undefined = cup.players[i];
        return p ? <Pop key={p.pid || i} style={styles.seat}><Face p={p} size={46} /><T w="heavy" size={10} color={p.you ? arena.gold : arena.text} numberOfLines={1}>{p.you ? "You" : p.name}</T></Pop>
          : <View key={i} style={styles.seat}><View style={styles.empty}><T w="heavy" size={18} color={arena.faint}>?</T></View><T w="bold" size={10} color={arena.faint}>Open</T></View>;
      })}
    </View> : <>
      <SectionTitle title="Bracket" action="Swipe ›" testID="cup-bracket-title" onAction={() => {}} />
      <Bracket cup={cup} onWatch={watch} />
    </>}

    <Panel flat testID="cup-code" style={styles.code}>
      <View style={styles.flex}>
        <T w="heavy" size={11} color={arena.aqua} style={styles.spaced}>WATCH CODE</T>
        <T testID="cup-code-text" w="heavy" size={28} color={arena.gold} style={styles.codeText}>{cup.code}</T>
        <T w="bold" size={11} color={arena.muted}><Icon name="eye" size={12} color={arena.muted} /> {cup.spectators}/{cup.max_spectators} watching with the code{cup.spectating ? " · you’re watching" : ""}</T>
      </View>
      <RaisedButton testID="cup-code-copy" tone="wine" height={44} accessibilityLabel="Copy watch code" style={styles.key} onPress={async () => { await Clipboard.setStringAsync(cup.code); setCopied(true); }}><Icon name={copied ? "check" : "content-copy"} size={20} color={arena.text} /></RaisedButton>
      <RaisedButton testID="cup-code-share" height={44} accessibilityLabel="Share the watch code on WhatsApp" style={styles.key} onPress={share}><Icon name="whatsapp" size={22} color={arena.text} /></RaisedButton>
    </Panel>
    {cup.invited_players?.length ? <View testID="cup-invited" style={styles.invitedList}>
      <SectionTitle title={`Invited (${cup.invited_players.length})`} />
      {cup.invited_players.map((p: Seat & { joined: boolean }) => <PersonRow key={p.pid || p.name} testID={`cup-invited-${p.pid}`} p={p} sub={`Level ${p.level}`}
        right={<T testID={`cup-invited-status-${p.pid}`} w="heavy" size={12} color={p.joined ? arena.online : arena.muted}>{p.joined ? "IN ✓" : "Invited"}</T>} />)}
      <RaisedButton testID="cup-remind" glyph="whatsapp" tone="wine" label="Remind on WhatsApp" onPress={remind} />
    </View> : null}
    <ErrorBox testID="cup-action-error" error={error} />
  </ScrollView>;

  const canJoin = cup && status === "open" && !cup.joined && (cup.kind === "open" || cup.invited);
  return <ArenaBg testID="cup-screen">
    <View style={[styles.frame, { paddingTop: insets.top + 6, paddingBottom: insets.bottom + 10 }]}>
      <View style={styles.top}>
        <CloseButton testID="cup-close" label="Close" onPress={back} />
        <View style={styles.flex}>
          <GoldTitle testID="cup-title">{cup ? `${cup.size}-Player Cup` : "Knockout Cup"}</GoldTitle>
          {cup ? <T testID="cup-meta" w="bold" size={12} color={arena.aqua} numberOfLines={1}>{cup.kind === "open" ? "Open" : "Friends"} · {cup.label}</T> : null}
        </View>
        <GameIcon name="trophy" size={42} />
      </View>
      {body}
      {cup && status === "open" ? <View style={styles.dock}>
        {canJoin ? <RaisedButton testID="cup-join" icon="swords" height={62} streak label="JOIN THE CUP" sub={`${cup.players.length}/${cup.size} in`} busy={busy === "join"} disabled={!!busy} onPress={() => act("join")} /> : null}
        {cup.is_host && cup.kind === "private" ? <RaisedButton testID="cup-start" icon="swords" height={62} streak label="START" sub={cup.can_start ? `${cup.players.length} players · empty seats become byes` : "Waiting for 1 friend to join"} busy={busy === "start"} disabled={!cup.can_start || !!busy} onPress={() => act("start")} /> : null}
        {cup.joined ? <RaisedButton testID="cup-leave" tone="wine" label={cup.is_host && cup.kind === "private" ? "Cancel cup" : "Leave"} busy={busy === "leave"} disabled={!!busy}
          onPress={() => (cup.is_host && cup.kind === "private" ? setConfirm(true) : act("leave"))} /> : null}
      </View> : null}
      {status === "finished" ? <View style={styles.dock}><RaisedButton testID="cup-again" icon="trophy" height={60} streak label="NEW CUP" sub="Win every round. Lift the cup." onPress={() => router.replace(go.cups())} /></View> : null}
    </View>
    <Sheet visible={confirm} onClose={() => setConfirm(false)} testID="cup-cancel-sheet">
      <GoldTitle size={22}>Cancel this cup?</GoldTitle>
      <T size={13} color={arena.muted}>Everyone you invited loses their seat. You can open a new cup any time.</T>
      <RaisedButton testID="cup-cancel-keep" label="Keep the cup" height={56} onPress={() => setConfirm(false)} />
      <RaisedButton testID="cup-cancel-confirm" tone="danger" label="Cancel cup" busy={busy === "leave"} onPress={() => { setConfirm(false); act("leave"); }} />
    </Sheet>
    {status === "finished" && champ?.you ? <Confetti count={40} /> : null}
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, stretch: { alignSelf: "stretch" }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 }, push: { marginLeft: "auto" },
  frame: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" },
  top: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, minHeight: 56 },
  middle: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 20 },
  content: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 12 },
  hero: { alignItems: "center", gap: 4, paddingVertical: 16, paddingHorizontal: 14 },
  live: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14, borderColor: arena.danger },
  seats: { flexDirection: "row", flexWrap: "wrap", rowGap: 10 }, seat: { width: "25%", alignItems: "center", gap: 3 },
  empty: { width: 46, height: 46, borderRadius: 23, alignItems: "center", justifyContent: "center", borderWidth: 2, borderStyle: "dashed", borderColor: arena.rimHi, backgroundColor: arena.panelEdge },
  fillTrack: { width: "70%", height: 8, borderRadius: 4, backgroundColor: arena.panelEdge, overflow: "hidden", marginVertical: 4 }, fillBar: { height: "100%", borderRadius: 4, backgroundColor: arena.tealHi },
  bracket: { gap: 14, paddingRight: 16 },
  col: { width: CARD_W, gap: 8 },
  colHead: { height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.rim }, colHeadOn: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
  colBody: { justifyContent: "space-around" }, slot: { justifyContent: "center" },
  match: { gap: 3, padding: 6, borderRadius: 14, backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim },
  matchLive: { borderColor: arena.danger }, matchMine: { borderColor: arena.tealHi },
  line: { flexDirection: "row", alignItems: "center", gap: 6, height: 30, paddingHorizontal: 6, borderRadius: 9, backgroundColor: arena.panelEdge },
  lineWon: { backgroundColor: arena.gold }, lineLost: { opacity: 0.45 },
  ghost: { width: 24, height: 24, borderRadius: 12, borderWidth: 1.5, borderStyle: "dashed", borderColor: arena.rim },
  matchFoot: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 2, minHeight: 22 },
  watch: { marginLeft: "auto", flexDirection: "row", alignItems: "center", gap: 3, height: 24, paddingHorizontal: 8, borderRadius: 12, backgroundColor: arena.teal, borderWidth: 1, borderColor: arena.tealOutline },
  link: { position: "absolute", right: -14, width: 14, height: SLOT / 2, borderRightWidth: 2, borderColor: arena.rim },
  linkDown: { top: "50%", borderTopWidth: 2, borderTopRightRadius: 8 }, linkUp: { bottom: "50%", borderBottomWidth: 2, borderBottomRightRadius: 8 },
  crown: { alignItems: "center", gap: 4, padding: 10, borderRadius: 18, backgroundColor: arena.panelHi, borderWidth: 1.5, borderColor: arena.gold },
  code: { flexDirection: "row", alignItems: "center", gap: 8, padding: 12 }, codeText: { letterSpacing: 6 }, key: { width: 48 },
  dock: { paddingHorizontal: 16, paddingTop: 8, gap: 10 }, invitedList: { gap: 8 },
});

export default withRapid(Cup, { banner: false });

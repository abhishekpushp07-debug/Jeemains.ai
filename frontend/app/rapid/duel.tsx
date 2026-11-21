import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, BackHandler, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeIn, ZoomIn, useReducedMotion } from "react-native-reanimated";
import { RF_BASE, rapidAccess, rf, uuid } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { invalidate } from "@/src/useCached";
import { CardClock } from "@/src/rapid/CardClock";
import { Avatar, EntryShow } from "@/src/components/Entry";
import { playSfx } from "@/src/sfx";
import { arena, rapidColors as colors, radius, space, rapidSubjectColor as subjectColor } from "@/src/theme";
import { GameIcon, GemColor } from "@/src/rapid/Art";
import { ArenaBg, CloseButton, GoldTitle, RaisedButton } from "@/src/rapid/arena";
import { RapidDiagram } from "@/src/rapid/Diagram";
import { Radar } from "@/src/rapid/juice";
import { Lineup, MatchPlayer, ScoreStrip, TeamBar, shownName } from "@/src/rapid/MatchParts";
import { MatchResult } from "@/src/rapid/MatchResult";
import { RapidText } from "@/src/rapid/RapidText";
import { GemFlare, gemAt, trailingStreak } from "@/src/rapid/StreakGem";
import { ErrorBox, Icon, Press, Sheet, T, buzz, tap, withRapid } from "@/src/rapid/ui";
import { go } from "@/src/rapid/social";
import { CARD_COUNTS, CARD_SECONDS, encodePicks, getCardCount, isBitsat, picksFrom, scopeLabel } from "@/src/rapid/scope";
import { ArenaWait, useArenaWait } from "@/src/rapid/ArenaWait";

const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());
type Params = { mode?: "random" | "ai"; subject?: string; chapter?: string; picks?: string; review?: string; did?: string; n?: string };

function Duel() {
  const p = useLocalSearchParams();
  return <Match key={JSON.stringify([p.r, p.did, p.review, p.mode, p.subject, p.chapter, p.picks])} />;
}

/** The wait before the entry show, ticking down every second on the server clock (a Cup Night lead-in is 30 s). */
function Soon({ at, now }: { at: number; now: () => number }) {
  const [t, setT] = useState(now);
  useEffect(() => {
    const iv = setInterval(() => setT(now()), 250);
    return () => clearInterval(iv);
  }, [now]);
  const left = Math.ceil(at - t);
  return left > 0 ? <T testID="duel-countdown-left" w="heavy" size={48} color={arena.gold}>{left}</T> : null;
}


/**
 * One match from start to finish: finding a rival (or waiting on a code), the entry show in step with the server clock,
 * 30, 50 or 100 cards against 1 to 4 rivals with the Phoenix streak, then the result. `did` opens a match seated by a Match Room, `review` an old one.
 */
function Match() {
  const p = useLocalSearchParams<Params>();
  const insets = useSafeAreaInsets(), router = useRouter(), reduced = useReducedMotion();
  const { user } = useAuth();
  const uid = user?.id || "", name = (user?.name || "Player").slice(0, 24);
  const [d, setD] = useState<any>(null);
  const [error, setError] = useState("");
  const [idx, setIdx] = useState(0);
  const [choice, setChoice] = useState<number | null>(null);
  const [fb, setFb] = useState<any>(null);
  const [clock, setClock] = useState(0);
  const [streak, setStreak] = useState(0);
  const [flare, setFlare] = useState<GemColor | null>(null);
  const [exit, setExit] = useState(false), [n, setN] = useState(0);
  const reqId = useRef(uuid());
  const scroll = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const anchor = useRef({ server: 0, mono: 0 });
  const startedAt = useRef(0), hold = useRef(0), sending = useRef(false), outcomes = useRef<string[]>([]);
  const serverNow = () => anchor.current.server + (mono() - anchor.current.mono) / 1000;
  // Live pushes leave out the cards once this phone has them ("lite"): keep the ones we already hold.
  const apply = useCallback((v: any) => { anchor.current = { server: v.server_now, mono: mono() }; setD((prev: any) => (v.cards === undefined && prev?.id === v.id ? { ...v, cards: prev.cards } : v)); }, []);
  const seat = useArenaWait(() => setN((x) => x + 1));

  // Open, create or join once per intent (request_id makes retries safe).
  useEffect(() => {
    let alive = true;
    if (!uid) return; // wait for sign-in to settle (a cold link would get a 401)
    const picks = picksFrom(p);
    const count = (CARD_COUNTS as readonly number[]).includes(Number(p.n)) ? Number(p.n) : getCardCount();
    const create = (mode: "random" | "invite") => rf<any>("/duels", uid, { method: "POST", body: { exam: "JEE", subject: picks[0].subject, picks, mode, name, count, request_id: reqId.current } });
    const run = p.review || p.did ? rf<any>(`/duels/${p.review || p.did}`, uid)
      // Practice Rival: open a private match and seat the rival at once, no waiting.
      : p.mode === "ai" ? create("invite").then((v) => (v.status === "waiting" ? rf<any>(`/duels/${v.id}/bot`, uid, { method: "POST", body: {} }) : v))
      : create("random");
    run.then((v) => alive && apply(v)).catch((e) => { if (alive && !seat.hold(e)) setError(e.message); });
    return () => { alive = false; };
  }, [p.mode, p.subject, p.chapter, p.picks, p.review, p.did, uid, name, apply, n]); // eslint-disable-line react-hooks/exhaustive-deps

  // Quick Match never leaves a student waiting alone: after a short search a practice rival takes the seat.
  useEffect(() => {
    if (d?.status !== "waiting" || d.mode !== "random") return;
    const t = setTimeout(() => { rf(`/duels/${d.id}/bot`, uid, { method: "POST", body: {} }).then(apply).catch(() => {}); }, 5000 + Math.random() * 2000);
    return () => clearTimeout(t);
  }, [d?.id, d?.status, d?.mode, uid, apply]);

  // Live connection: the server pushes joins and score changes at once. If the socket drops, a slow poll keeps the match going.
  const over = !d?.id || d.status === "finished" || d.status === "cancelled" || d.status === "expired";
  useEffect(() => {
    if (over) return;
    let ws: WebSocket | null = null, live = false, stop = false, tries = 0;
    let retry: ReturnType<typeof setTimeout> | undefined;
    const connect = () => {
      ws = new WebSocket(`${RF_BASE.replace(/^http/, "ws")}/duels/${d.id}/ws`);
      ws.onopen = () => { rapidAccess(uid).then((token) => { if (!stop && ws?.readyState === WebSocket.OPEN) { ws.send(JSON.stringify({ token, lite: 1 })); live = true; tries = 0; } }).catch(() => ws?.close()); };
      ws.onmessage = (e) => { try { apply(JSON.parse(e.data)); } catch { /* not a state frame */ } };
      // Back off with a random spread: after a server restart, thousands of phones must not reconnect in the same instant.
      ws.onclose = () => { live = false; if (!stop) retry = setTimeout(connect, Math.min(15000, 1500 * 2 ** tries++) * (0.6 + Math.random() * 0.8)); };
      ws.onerror = () => ws?.close();
    };
    connect();
    const ping = setInterval(() => { if (live) ws?.send("p"); }, 20000);
    const poll = setInterval(() => { if (!live) rf(`/duels/${d.id}`, uid).then(apply).catch(() => {}); }, 2500 + Math.random() * 1000);
    return () => { stop = true; clearTimeout(retry); clearInterval(ping); clearInterval(poll); ws?.close(); };
  }, [d?.id, over, uid, apply]);

  const players: MatchPlayer[] = d?.players || [];
  const me = players.find((x) => x.you), opp = players.find((x) => !x.you);
  const total = d?.total || 30, limit = (d?.seconds_per_card || CARD_SECONDS) * 1000;
  const ready = d?.status === "ready";
  // The entry show runs on the server clock and ends exactly when card 1 opens, on every phone.
  const showStart = ready ? d.start_at - d.entry_seconds : 0;
  useEffect(() => {
    if (!ready) return;
    const now = serverNow();
    setClock(now);
    const timers = [showStart, d.start_at].filter((at) => at > now).map((at) => setTimeout(() => setClock(serverNow() + 0.05), (at - now) * 1000));
    return () => timers.forEach(clearTimeout);
  }, [ready, d?.id, d?.start_at]); // eslint-disable-line react-hooks/exhaustive-deps
  const started = ready && clock >= d.start_at;
  const showing = ready && !started && clock >= showStart;
  const card = started ? d.cards?.[idx] : null;
  const verdict = fb && fb.index === idx ? fb : null;
  const playing = started && !!card;

  useEffect(() => {
    // After a reconnect: pick up where the server says we are, without cutting a visible verdict short.
    const mine = me?.answers || [];
    if (mine.length > outcomes.current.length) { outcomes.current = mine.map((a) => a.outcome); setStreak(trailingStreak(mine)); }
    if (me && me.answered > idx && !fb && choice === null && !sending.current) setIdx(me.answered);
  }, [me?.answered, fb, choice]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!card) return;
    startedAt.current = mono();
    setChoice(null);
    setFb(null);
    scroll.current?.scrollTo({ y: 0, animated: false });
  }, [card?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback(async (kind: "answer" | "skipped" | "timed_out", c: number | null) => {
    if (!d || sending.current || !card) return;
    sending.current = true;
    const ms = Math.min(limit, Math.round(mono() - startedAt.current));
    try {
      const r = await rf<any>(`/duels/${d.id}/answer`, uid, { method: "POST", body: { index: idx, choice: c, outcome: kind, ms } });
      outcomes.current[r.index] = r.outcome;
      const run = trailingStreak(outcomes.current.slice(0, r.index + 1).map((outcome) => ({ outcome })));
      setStreak(run);
      setFb(r);
      const ok = r.outcome === "correct", gem = ok ? gemAt(run) : null;
      // A diamond is won in the gap before the next card, never on top of a question.
      if (gem) setFlare(gem);
      else if (kind === "answer") { playSfx(ok ? "correct" : "wrong", 0.8); buzz(ok ? "success" : "error"); }
      else if (kind === "timed_out") { playSfx("wrong", 0.6); buzz("warning"); }
      setTimeout(() => { setChoice(null); setFb(null); setIdx((i) => Math.max(i, r.index + 1)); }, kind === "answer" ? 1100 : 700);
    } catch (e: any) {
      // Unlock the card so the student can tap again (the timer waits a moment before it retries a time-out).
      hold.current = mono() + 1500;
      setChoice(null);
      setError(e.message + " Tap again to retry.");
      setTimeout(() => setError(""), 3000);
    } finally { sending.current = false; }
  }, [d, card, idx, uid, limit]);

  // Time is up on the card in view. The ring keeps its own seconds (CardClock), so a tick never redraws the card.
  // After a failed send the time-out waits a moment before it is sent again (the clock asks again every 100 ms).
  const expire = () => {
    if (mono() < hold.current) return false;
    setChoice(-1);
    send("timed_out", null);
  };

  const won = d?.winner === d?.you;
  useEffect(() => {
    if (d?.status !== "finished" || p.review) return;
    ["rfduels", "rfprofile", "rfboard", "revision", "rfplayer", "rfgang", "rfh2h"].forEach((k) => invalidate(`u.${uid}.${k}`));
    playSfx(won ? "win" : d.winner === "tie" ? "go" : "lose");
    buzz(won ? "success" : "warning");
  }, [d?.status, uid]); // eslint-disable-line react-hooks/exhaustive-deps

  // A cup match opened from a link has nothing behind it: go to its bracket, not the lobby.
  const back = () => (router.canGoBack() ? router.back() : router.replace(d?.cup_id ? go.cup(d.cup_id) : "/(tabs)/rapid"));
  const leave = () => {
    if (d?.status === "waiting") rf(`/duels/${d.id}/cancel`, uid, { method: "POST", body: {} }).catch(() => {});
    back();
  };
  const inMatch = ready && !me?.done;
  const close = () => (inMatch ? setExit(true) : leave());
  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { close(); return true; });
    return () => sub.remove();
  }, [inMatch, d?.status])); // eslint-disable-line react-hooks/exhaustive-deps

  const subject = d?.subject || p.subject || "Physics";
  const picks = d?.picks || picksFrom(p), label = d?.label || scopeLabel(picks);
  const tint = subjectColor(card?.subject || subject);
  const quick = () => router.replace(go.duel({ mode: "random", picks: encodePicks(picks), r: uuid() }));
  // On your own phone you enter first, then the others in the order they joined.
  const entrants = me ? [me, ...players.filter((x) => !x.you)] : players;

  let body: React.ReactNode = null;
  if (!d) {
    body = seat.waiting ? <ArenaWait testID="duel-arena-wait" left={seat.left} onCancel={() => { seat.cancel(); back(); }} />
      : error ? <View style={styles.middle}><ErrorBox testID="duel-error" error={error} retry={() => { setError(""); setN((x) => x + 1); }} /><RaisedButton testID="duel-back" tone="wine" label="Back to the Arena" onPress={back} style={styles.stretch} /></View>
      : <View style={styles.middle} testID="duel-loading"><ActivityIndicator color={arena.aqua} size="large" /><T w="bold" color={arena.muted}>Setting up your match…</T></View>;
  } else if (d.status === "waiting" && d.mode === "random") {
    body = <View style={styles.middle} testID="duel-waiting">
      <Radar size={250}><Avatar icon={me?.avatar} frame={me?.frame} size={104} /></Radar>
      <GoldTitle size={26} center testID="duel-searching">Finding a rival…</GoldTitle>
      <T w="bold" size={13} color={arena.aqua} style={styles.center}>{label}</T>
      <T size={12} color={arena.muted} style={styles.center}>A practice rival steps in if nobody is free.</T>
      <RaisedButton testID="duel-cancel-search" tone="wine" label="Cancel" onPress={leave} style={styles.stretch} />
    </View>;
  } else if (d.status === "waiting") {
    // A Practice Rival match whose rival has not sat down yet (a slow network): seat it again.
    body = <View style={styles.middle} testID="duel-waiting">
      <Radar size={220}><Avatar icon={me?.avatar} frame={me?.frame} size={96} /></Radar>
      <GoldTitle size={24} center>Calling your rival…</GoldTitle>
      <RaisedButton testID="duel-seat-rival" icon="rival" label="Start now" onPress={() => rf(`/duels/${d.id}/bot`, uid, { method: "POST", body: {} }).then(apply).catch((e) => setError(e.message))} style={styles.stretch} />
      <ErrorBox testID="duel-error" error={error} />
      <RaisedButton testID="duel-cancel-search" tone="wine" label="Cancel" onPress={leave} style={styles.stretch} />
    </View>;
  } else if (d.status === "expired" || d.status === "cancelled") {
    body = <View style={styles.middle} testID="duel-closed">
      <GameIcon name="rival" size={92} />
      <GoldTitle size={26} center>Nobody joined this time</GoldTitle>
      <T size={13} color={arena.muted} style={styles.center}>A rival is always ready in Quick Match.</T>
      <RaisedButton testID="duel-quick-match" icon="swords" height={60} label="Quick Match" onPress={quick} style={styles.stretch} />
      <RaisedButton testID="duel-back" tone="wine" label="Back to the Arena" onPress={back} style={styles.stretch} />
    </View>;
  } else if (ready && !started) {
    body = <View style={styles.middle} testID="duel-countdown">
      <Lineup players={entrants} />
      <GoldTitle size={26} center>Get ready…</GoldTitle>
      <Soon at={showStart} now={serverNow} />
      <T testID="duel-countdown-rules" size={13} color={arena.muted} style={styles.center}>Same {total} cards for everyone · {limit / 1000} s each · +1 per correct</T>
    </View>;
  } else if (playing) {
    const locked = choice !== null;
    const edge = verdict ? (verdict.outcome === "correct" ? colors.success : verdict.outcome === "incorrect" ? colors.error : colors.warning) : tint + "66";
    body = <View style={styles.flex} testID="duel-play">
      <View style={styles.strip}>
        {d.team_mode ? <TeamBar teams={d.teams} mine={d.my_team} /> : null}
        <ScoreStrip players={players} total={total} streak={streak} />
        {opp?.forfeit && players.length === 2 ? <View testID="duel-opponent-left" style={styles.leftNote}><T w="heavy" size={12} color={arena.badgeInk} style={styles.center}>{shownName(opp)} left. Finish your cards to take the win!</T></View> : null}
      </View>
      <ScrollView ref={scroll} style={styles.flex} contentContainerStyle={styles.cardArea} showsVerticalScrollIndicator={false}>
        <Animated.View key={card.id} entering={reduced ? undefined : FadeIn.duration(160)} testID="duel-card" style={[styles.questionCard, { borderColor: edge }]}>
          <View style={styles.cardTop}>
            <T w="bold" size={11} color={colors.muted} numberOfLines={1} style={styles.flex}>{card.chapter}</T>
            {verdict ? <Animated.View entering={reduced ? undefined : ZoomIn.duration(200)} testID="duel-verdict" style={[styles.verdict, { backgroundColor: edge }]}>
              <Icon name={verdict.outcome === "correct" ? "check-bold" : verdict.outcome === "incorrect" ? "close-thick" : "timer-sand-complete"} size={16} color={arena.badgeInk} />
              <T w="heavy" size={13} color={arena.badgeInk}>{verdict.outcome === "correct" ? "RIGHT +1" : verdict.outcome === "incorrect" ? "WRONG" : verdict.outcome === "timed_out" ? "TIME UP" : "SKIPPED"}</T>
            </Animated.View> : null}
          </View>
          <RapidText text={card.prompt} size={20} testID="duel-card-prompt" />
          <RapidDiagram diagram={card.diagram} testID="duel-card-diagram" />
          {verdict?.formula ? <View style={styles.formula}><RapidText text={verdict.formula} size={20} testID="duel-card-formula" /></View> : null}
          <View style={styles.options}>
            {card.options.map((o: string, k: number) => {
              const isAns = verdict && k === verdict.answer, picked = k === choice;
              const bg = isAns ? colors.custom_successSoft : verdict && picked ? colors.custom_errorSoft : picked ? colors.custom_infoSoft : colors.surfaceSecondary;
              const bd = isAns ? colors.success : verdict && picked ? colors.error : picked ? colors.brandPrimary : colors.border;
              return <Press key={k} testID={"duel-option-" + k} disabled={locked} haptic={false} onPress={() => { tap("medium"); setChoice(k); send("answer", k); }} accessibilityLabel={o} style={[styles.option, { borderColor: bd, backgroundColor: bg }]}>
                <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
                <View style={styles.optionText}><RapidText text={o} size={16} testID={`duel-option-text-${k}`} /></View>
                {isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : verdict && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
              </Press>;
            })}
          </View>
          {verdict?.explain ? <RapidText testID="duel-feedback-explanation" text={verdict.explain} size={14} /> : null}
        </Animated.View>
      </ScrollView>
      <View style={styles.dock}>
        <ErrorBox testID="duel-answer-error" error={error} />
        <RaisedButton testID="duel-skip" tone="wine" glyph="skip-next-outline" label="Skip this card" disabled={locked} onPress={() => { setChoice(-1); send("skipped", null); }} />
      </View>
    </View>;
  } else if (ready) {
    body = <View style={styles.middle} testID="duel-wait-opponent">
      <ScoreStrip players={players} total={total} />
      <ActivityIndicator color={arena.aqua} size="large" />
      <GoldTitle size={24} center>You’re done!</GoldTitle>
      <T w="bold" size={13} color={arena.muted} style={styles.center}>{players.length > 2 ? "Waiting for the others to finish…" : `Waiting for ${shownName(opp)} to finish…`}</T>
    </View>;
  } else if (d.status === "finished") {
    body = <MatchResult d={d} uid={uid} historical={!!p.review} onDone={d.cup_id && !p.review ? () => router.replace(go.cup(d.cup_id)) : back} />;
  }

  return <ArenaBg dim={playing} testID="duel-screen">
    <View style={[styles.frame, { paddingTop: insets.top + 6, paddingBottom: insets.bottom + 10 }]}>
      <View style={styles.top}>
        <CloseButton testID="duel-exit-button" label={inMatch ? "Leave match" : "Close"} onPress={close} />
        <View style={styles.flex}>
          <T testID="duel-exam-group" w="heavy" size={12} color={arena.aqua} numberOfLines={1}>{(d?.cup_id ? "KNOCKOUT CUP · " : d?.team_mode ? "GANG WAR · " : "") + (picks.length && picks.every((x: { subject: string }) => isBitsat(x.subject)) ? "BITSAT · " : "") + label.toUpperCase()}</T>
          <T testID="duel-card-counter" w="heavy" size={17} color={arena.text} numberOfLines={1}>{playing ? `Card ${idx + 1} / ${total}` : d?.status === "finished" ? (p.review ? "Match review" : "Match result") : d?.team_mode ? "Gang vs Gang" : players.length > 2 ? `${players.length}-player match` : "1 v 1 match"}</T>
        </View>
        {d?.watchers && d.status === "ready" ? <View testID="duel-watchers" style={styles.watchers}><Icon name="eye" size={14} color={arena.aqua} /><T w="heavy" size={11} color={arena.aqua}>{d.watchers}</T></View> : null}
        {playing ? <CardClock key={card.id} startedAt={startedAt} limit={limit} running={choice === null && !fb} color={tint} onExpire={expire} /> : <GameIcon name="swords" size={42} />}
      </View>
      {body}
    </View>
    {showing ? <EntryShow key={d.id} testID="duel-entry-show" players={entrants} elapsed={Math.max(0, clock - showStart)} /> : null}
    {flare ? <GemFlare key={`${idx}-${flare}`} color={flare} onDone={() => setFlare(null)} /> : null}
    <Sheet visible={exit} onClose={() => setExit(false)} testID="duel-exit-sheet">
      <GoldTitle size={22}>Leave the match?</GoldTitle>
      <T size={13} color={arena.muted}>Unanswered cards score 0, you finish last, and this match’s diamonds are lost. The others keep playing.</T>
      <RaisedButton testID="duel-exit-stay" label="Keep playing" height={56} onPress={() => setExit(false)} />
      <RaisedButton testID="duel-exit-confirm" tone="danger" label="Leave match" onPress={() => { setExit(false); if (d?.id) rf(`/duels/${d.id}/forfeit`, uid, { method: "POST", body: {} }).catch(() => {}); back(); }} />
    </Sheet>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, stretch: { alignSelf: "stretch" }, center: { textAlign: "center" }, spaced: { letterSpacing: 3 },
  frame: { flex: 1, width: "100%", maxWidth: 560, alignSelf: "center" },
  top: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, minHeight: 58 },
  middle: { flex: 1, alignItems: "center", justifyContent: "center", gap: 14, paddingHorizontal: 20 },
  content: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 16, gap: 12 },
  watchers: { flexDirection: "row", alignItems: "center", gap: 3, paddingHorizontal: 8, height: 26, borderRadius: 13, backgroundColor: arena.panelEdge, borderWidth: 1, borderColor: arena.rim },
  strip: { paddingHorizontal: 16, paddingTop: 4, gap: 6 },
  leftNote: { padding: space.sm, borderRadius: radius.md, backgroundColor: arena.online },
  cardArea: { flexGrow: 1, justifyContent: "center", paddingHorizontal: 16, paddingVertical: space.md },
  questionCard: { backgroundColor: colors.custom_reading, borderRadius: 26, padding: 18, gap: 14, borderWidth: 1.5, shadowColor: arena.black, shadowOpacity: 0.35, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 5 },
  cardTop: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 28 },
  verdict: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 10, height: 28, borderRadius: 14 },
  formula: { padding: 14, backgroundColor: colors.surface, borderRadius: 14 },
  options: { gap: space.sm },
  option: { minHeight: 52, borderRadius: radius.md, borderWidth: 2, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm },
  optionText: { flex: 1, paddingVertical: 12 },
  dock: { paddingHorizontal: 16, paddingTop: 6, gap: 8 },
});

export default withRapid(Duel, { banner: false });

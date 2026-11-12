import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Linking, ScrollView, Share, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Clipboard from "expo-clipboard";
import Animated, { FadeIn, ZoomIn, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { RF_BASE, rf, uuid, rapidAccess } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { Button, Card, ErrorBox, Icon, Press, Sheet, T, tap, buzz } from "@/src/rapid/ui";
import { Art } from "@/src/rapid/Art";
import { RapidText } from "@/src/rapid/RapidText";
import { playSfx } from "@/src/sfx";
import { Ring } from "@/src/components/Ring";
import { RewardPanel } from "@/src/components/game";
import { Avatar, EntryShow } from "@/src/components/Entry";
import { BattleHero } from "@/src/components/BattleHero";
import { RapidDiagram as BiologyDiagram } from "@/src/rapid/Diagram";
import { rapidColors as colors, radius, space, rapidSubjectColor as subjectColor } from "@/src/theme";

const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());
const LIMIT = 20000;

export function playerName(phone?: string) {
  return phone ? "Player ··" + phone.slice(-4) : "Player";
}

function inviteText(code: string, subject: string) {
  return `⚡ Rapid Fire duel on JEECIRCLE.AI! ${subject} · 30 formula cards · 20 s each.\nJoin with code: ${code}\nOpen JEECIRCLE.AI → Rapid Fire → Join with code. Free for everyone: https://jeelive.ai`;
}

export async function shareOnWhatsApp(code: string, subject: string) {
  const text = inviteText(code, subject);
  try {
    await Linking.openURL("whatsapp://send?text=" + encodeURIComponent(text));
  } catch {
    try {
      await Linking.openURL("https://wa.me/?text=" + encodeURIComponent(text));
    } catch {
      Share.share({ message: text }).catch(() => {});
    }
  }
}

export default function Duel() {
  const p = useLocalSearchParams();
  return <DuelRound key={JSON.stringify([p.r, p.review, p.mode, p.code, p.subject, p.chapter, p.exam])} />;
}

function DuelRound() {
  const p = useLocalSearchParams<{ mode: "random" | "invite" | "join" | "ai"; exam?: "JEE" | "NEET"; subject?: string; chapter?: string; code?: string; review?: string }>();
  const reduced = useReducedMotion();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const uid = user?.id || "";
  const name = playerName(user?.phone);
  const [d, setD] = useState<any>(null);
  const [error, setError] = useState(() => (p.exam && p.exam !== "JEE") || p.subject === "Biology" ? "This practice is archived. Return to JEE Main Rapid Fire." : "");
  const [idx, setIdx] = useState(0);
  const [choice, setChoice] = useState<number | null>(null);
  const [fb, setFb] = useState<any>(null);
  const [left, setLeft] = useState(LIMIT);
  const [now, setNow] = useState(0);
  const [exit, setExit] = useState(false);
  const [copied, setCopied] = useState(false);
  const [n, setN] = useState(0);
  const [intro, setIntro] = useState("");
  const [reviewMisses, setReviewMisses] = useState(false);
  const reqId = useRef(uuid());
  const playScroll = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const anchor = useRef({ server: 0, mono: 0 });
  const startedAt = useRef(0);
  const sending = useRef(false);
  const serverNow = () => anchor.current.server + (mono() - anchor.current.mono) / 1000;
  const apply = useCallback((v: any) => {
    anchor.current = { server: v.server_now, mono: mono() };
    setD(v);
  }, []);

  // Create / join once per intent (request_id makes retries idempotent).
  useEffect(() => {
    let alive = true;
    if (!uid) return; // wait for auth hydration (cold deep-link from an invite would 401)
    if ((p.exam && p.exam !== "JEE") || p.subject === "Biology") {
      return;
    }
    const run = p.review ? rf(`/duels/${p.review}`, uid)
      : p.mode === "join"
      ? rf("/duels/join", uid, { method: "POST", body: { code: p.code || "", name, exam: "JEE" } })
      : p.mode === "ai"
        // Straight to an AI Rival: open a private duel and seat the rival at once (no queue wait).
        ? rf<any>("/duels", uid, { method: "POST", body: { exam: "JEE", subject: p.subject || "Physics", chapter: p.chapter || null, mode: "invite", name, request_id: reqId.current } })
            .then((v) => (v.status === "waiting" ? rf(`/duels/${v.id}/bot`, uid, { method: "POST", body: {} }) : v))
        : rf("/duels", uid, { method: "POST", body: { exam: "JEE", subject: p.subject || "Physics", chapter: p.chapter || null, mode: p.mode, name, request_id: reqId.current } });
    run.then((v) => alive && apply(v)).catch((e) => alive && setError(e.message));
    return () => { alive = false; };
  }, [p.mode, p.code, p.subject, p.chapter, p.exam, p.review, uid, name, apply, n]);

  // Quick match never leaves a student waiting alone: after a short search an arena player takes the seat.
  useEffect(() => {
    if (d?.status !== "waiting" || d.mode !== "random") return;
    const t = setTimeout(() => { rf(`/duels/${d.id}/bot`, uid, { method: "POST", body: {} }).then(apply).catch(() => {}); }, 5000 + Math.random() * 2500);
    return () => clearTimeout(t);
  }, [d?.id, d?.status, d?.mode, uid, apply]);

  // Live connection: the server pushes opponent joins and score changes instantly.
  // If the socket drops, a slow poll keeps the duel going while we reconnect.
  const over = !d?.id || d.status === "finished" || d.status === "cancelled" || d.status === "expired";
  useEffect(() => {
    if (over) return;
    let ws: WebSocket | null = null, live = false, stop = false;
    let retry: ReturnType<typeof setTimeout> | undefined;
    const connect = () => {
      ws = new WebSocket(`${RF_BASE.replace(/^http/, "ws")}/duels/${d.id}/ws`);
      ws.onopen = () => { rapidAccess(uid).then(token => { if (!stop && ws?.readyState === WebSocket.OPEN) { ws.send(JSON.stringify({ token })); live = true; } }).catch(() => ws?.close()); };
      ws.onmessage = (e) => { try { apply(JSON.parse(e.data)); } catch {} };
      ws.onclose = () => { live = false; if (!stop) retry = setTimeout(connect, 2000); };
      ws.onerror = () => ws?.close();
    };
    connect();
    const ping = setInterval(() => { if (live) ws?.send("p"); }, 20000);
    const poll = setInterval(() => { if (!live) rf(`/duels/${d.id}`, uid).then(apply).catch(() => {}); }, 3000);
    return () => { stop = true; clearTimeout(retry); clearInterval(ping); clearInterval(poll); ws?.close(); };
  }, [d?.id, over, uid, apply]);

  const me = d?.players?.find((x: any) => x.you);
  const opp = d?.players?.find((x: any) => !x.you);
  // First card waits for both the server start time and the full 4 s entry show.
  const started = d?.status === "ready" && d.start_at && now >= d.start_at && intro === d.id;
  useEffect(() => {
    if (started || over) return;
    const iv = setInterval(() => setNow(serverNow()), 250);
    return () => clearInterval(iv);
  }, [started, over]);
  const total = d?.total || 30;
  const card = d?.cards?.[idx];
  const verdict = fb && fb.index === idx ? fb : null;

  useEffect(() => {
    // Resync after reconnect, but never cut the visible RIGHT/WRONG verdict short.
    if (me && me.answered > idx && !fb && choice === null && !sending.current) setIdx(me.answered);
  }, [me?.answered, fb, choice]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!started || !card) return;
    startedAt.current = mono();
    // Reset card controls once without remounting offline maths views.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChoice(null);
    setFb(null);
    setLeft(LIMIT);
    playScroll.current?.scrollTo({ y: 0, animated: false });
  }, [started, card?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback(async (outcome: "answer" | "skipped" | "timed_out", c: number | null) => {
    if (!d || sending.current || !card) return;
    sending.current = true;
    const ms = Math.min(LIMIT, Math.round(mono() - startedAt.current));
    try {
      const r = await rf(`/duels/${d.id}/answer`, uid, { method: "POST", body: { index: idx, choice: c, outcome, ms } });
      setFb(r);
      if (outcome === "answer") { const ok = r.outcome === "correct"; playSfx(ok ? "correct" : "wrong", 0.8); buzz(ok ? "success" : "error"); }
      setTimeout(() => { setChoice(null); setFb(null); setIdx((i) => Math.max(i, r.index + 1)); }, outcome === "answer" ? 1100 : 600);
    } catch (e: any) {
      // Unlock the card so the student can retry (or the timer can still expire).
      setChoice(null);
      setError(e.message + " Tap again to retry.");
      setTimeout(() => setError(""), 3000);
    } finally {
      sending.current = false;
    }
  }, [d, card, idx, uid]);

  useEffect(() => {
    if (!started || !card || choice !== null || fb) return;
    const iv = setInterval(() => {
      const l = LIMIT - (mono() - startedAt.current);
      setLeft(previous => Math.ceil(previous / 1000) === Math.ceil(Math.max(0, l) / 1000) ? previous : Math.max(0, l));
      if (l <= 0) {
        setChoice(-1);
        send("timed_out", null);
      }
    }, 100);
    return () => clearInterval(iv);
  }, [started, card?.id, choice, fb, send]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (d?.status !== "finished" || p.review) return;
    invalidate(`u.${uid}.duels`);
    invalidate(`u.${uid}.rfprofile`);
    invalidate(`u.${uid}.rfboard`);
    invalidate(`u.${uid}.revision`);
    const won = d.winner === d.you;
    playSfx(won ? "win" : d.winner === "tie" ? "go" : "lose");
    buzz(won ? "success" : "warning");
  }, [d?.status, uid]); // eslint-disable-line react-hooks/exhaustive-deps

  function leave() {
    if (d?.status === "waiting") rf(`/duels/${d.id}/cancel`, uid, { method: "POST", body: {} }).catch(() => {});
    router.back();
  }
  const tint = subjectColor(d?.subject || p.subject);

  let body: React.ReactNode = null;
  if (!d) {
    body = error ? <View style={{ padding: space.lg, gap: space.md }}><ErrorBox error={error} retry={() => setN((x) => x + 1)} testID="duel-error" /><Button testID="duel-back" kind="secondary" label="Back" onPress={() => router.back()} /></View>
      : <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.md }}><ActivityIndicator color={tint} size="large" /><T w="bold" color={colors.onSurfaceInverse}>{p.mode === "join" ? "Joining duel…" : "Setting up your duel…"}</T></View>;
  } else if (d.status === "waiting" || d.status === "expired" || d.status === "cancelled") {
    const invite = d.mode === "invite";
    body = (
      <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.lg }} testID="duel-waiting">
        <BattleHero me={{ avatar: me?.avatar, frame: me?.frame, entry: me?.entry }} chapterPill={null}
          subjects={
            <View style={{ alignItems: "center", gap: 6 }}>
              {d.status === "waiting" ? <ActivityIndicator color={colors.custom_neonAmber} /> : <Icon name="account-clock-outline" size={32} color={colors.custom_gameMuted} />}
              <T w="heavy" size={19} color={colors.onSurfaceInverse} style={{ textAlign: "center" }}>{d.status !== "waiting" ? "No opponent joined" : invite ? "Waiting for your friend…" : `Finding a ${d.subject} opponent…`}</T>
              <T size={13} color={colors.custom_gameMuted} style={{ textAlign: "center" }}>{d.status !== "waiting" ? "Nobody joined this time. Try a quick match or play solo." : invite ? "Share the code. The duel starts the moment they join." : "Looking for a player. A practice rival may join if nobody is available."}</T>
            </View>
          } />
        {invite && d.status === "waiting" ? (
          <Card style={{ alignItems: "center", gap: space.md }} testID="duel-invite-card">
            <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>DUEL CODE</T>
            <T w="heavy" size={38} style={{ letterSpacing: 6 }} testID="duel-code">{d.code}</T>
            <Button testID="duel-share-whatsapp" label="Send on WhatsApp" icon="whatsapp" color={colors.success} onPress={() => shareOnWhatsApp(d.code, d.subject)} style={{ alignSelf: "stretch" }} />
            <Button testID="duel-copy-code" kind="secondary" icon={copied ? "check" : "content-copy"} label={copied ? "Copied" : "Copy code"} onPress={async () => { await Clipboard.setStringAsync(d.code); setCopied(true); }} style={{ alignSelf: "stretch" }} />
          </Card>
        ) : null}
        {!invite || d.status !== "waiting" ? (
          <Button testID="duel-invite-instead" kind="secondary" icon="whatsapp" label="Invite a WhatsApp friend instead" onPress={() => { leave(); router.push({ pathname: "/rapid/duel", params: { mode: "invite", exam: d.exam, subject: d.subject, chapter: d.chapter || "" } }); }} />
        ) : (
          <Button testID="duel-quick-match-instead" icon="sword-cross" label="Quick match instead" color={colors.custom_amber} onPress={() => { rf(`/duels/${d.id}/cancel`, uid, { method: "POST", body: {} }).catch(() => {}); router.replace({ pathname: "/rapid/duel", params: { mode: "random", exam: d.exam, subject: d.subject, chapter: d.chapter || "", r: uuid() } }); }} />
        )}
        <Button testID="duel-play-solo" kind="ghost" label="Play solo instead" onPress={() => { leave(); router.push({ pathname: "/rapid/session", params: { exam: d.exam, subject: d.subject, chapter: d.chapter || "" } }); }} />
      </ScrollView>
    );
  } else if (d.status === "ready" && !started) {
    const c = Math.min(5, Math.max(1, Math.ceil(d.start_at - now)));
    body = (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.lg, paddingHorizontal: space.lg }} testID="duel-countdown">
        <VersusRow me={me} opp={opp} tint={tint} total={total} />
        <Animated.View key={c} entering={reduced ? undefined : ZoomIn.duration(250)}><T w="heavy" size={88} color={colors.custom_neonAmber}>{c}</T></Animated.View>
        <T testID="duel-countdown-rules" size={13} color={colors.custom_gameMuted}>Same 30 cards · 20 s each · +1 score per correct</T>
      </View>
    );
  } else if (d.status === "ready" && card) {
    const locked = choice !== null;
    body = (
      <ScrollView ref={playScroll} style={styles.playScroll} contentContainerStyle={styles.playContent} testID="duel-play">
        <VersusRow me={me} opp={opp} tint={tint} total={total} />
        {opp?.forfeit ? <View testID="duel-opponent-left" style={{ padding: space.sm, borderRadius: radius.md, backgroundColor: colors.custom_neonGreen }}><T w="heavy" size={13} color={colors.custom_gameBg} style={{ textAlign: "center" }}>{opp.name || "Your rival"} left the duel. Finish your cards to claim the win!</T></View> : null}
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginVertical: space.sm }}>
          <T w="heavy" size={15} color={colors.onSurfaceInverse} testID="duel-card-counter">Card {idx + 1} / {total}</T>
          <Ring light left={left} color={tint} />
        </View>
        <Animated.View entering={reduced ? undefined : FadeIn.duration(160)} testID="duel-card" style={[styles.questionCard, { borderColor: verdict ? (verdict.outcome === "correct" ? colors.success : verdict.outcome === "incorrect" ? colors.error : colors.warning) : tint + "66" }]}>
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <T w="bold" size={11} color={colors.muted}>{card.chapter}</T>
            {verdict ? (
              <Animated.View entering={reduced ? undefined : ZoomIn.duration(200)} testID="duel-verdict" style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 10, height: 28, borderRadius: 14, backgroundColor: verdict.outcome === "correct" ? colors.success : verdict.outcome === "incorrect" ? colors.error : colors.warning }}>
                <Icon name={verdict.outcome === "correct" ? "check-bold" : verdict.outcome === "incorrect" ? "close-thick" : "timer-sand-complete"} size={16} color={colors.onSuccess} />
                <T w="heavy" size={13} color={colors.onSuccess}>{verdict.outcome === "correct" ? "RIGHT +1" : verdict.outcome === "incorrect" ? "WRONG" : "MISSED"}</T>
              </Animated.View>
            ) : null}
          </View>
          <RapidText text={card.prompt} size={20} testID="duel-card-prompt" />
          <BiologyDiagram diagram={card.diagram} testID="duel-card-diagram" />
          {verdict?.formula ? <View style={styles.formula}><RapidText text={verdict.formula} size={21} testID="duel-card-formula" /></View> : null}
          {card.options.map((o: string, k: number) => {
            const isAns = verdict && k === verdict.answer, picked = k === choice;
            const bg = isAns ? colors.custom_successSoft : verdict && picked ? colors.custom_errorSoft : picked ? colors.custom_infoSoft : colors.surfaceSecondary;
            const bd = isAns ? colors.success : verdict && picked ? colors.error : picked ? colors.brandPrimary : colors.border;
            return (
              <Press key={k} testID={"duel-option-" + k} disabled={locked} haptic={false} onPress={() => { tap("medium"); setChoice(k); send("answer", k); }} accessibilityLabel={o}
                style={{ minHeight: 50, borderRadius: radius.md, borderWidth: 2, borderColor: bd, backgroundColor: bg, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm }}>
                <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
                <View style={styles.optionText}><RapidText text={o} size={16} testID={`duel-option-text-${k}`} /></View>
                {isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : verdict && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
              </Press>
            );
          })}
          {verdict ? <View style={styles.feedback}><T w="heavy" size={14} testID="duel-feedback" color={verdict.outcome === "correct" ? colors.success : verdict.outcome === "incorrect" ? colors.error : colors.warning}>{verdict.outcome === "correct" ? "Correct +1" : verdict.outcome === "incorrect" ? "Incorrect" : verdict.outcome === "timed_out" ? "Timed out" : "Skipped"}</T>{verdict.explain ? <RapidText testID="duel-feedback-explanation" text={verdict.explain} size={14} /> : null}</View> : null}
        </Animated.View>
        <View style={{ flexDirection: "row", gap: space.sm, paddingVertical: space.md }}>
          <Button testID="duel-skip" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={() => { setChoice(-1); send("skipped", null); }} style={{ flex: 1 }} />
        </View>
        <ErrorBox error={error} />
      </ScrollView>
    );
  } else if (d.status === "ready") {
    body = (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.md, padding: space.lg }} testID="duel-wait-opponent">
        <VersusRow me={me} opp={opp} tint={tint} total={total} />
        <ActivityIndicator color={tint} />
        <T w="bold" color={colors.onSurfaceInverse} style={{ textAlign: "center" }}>You’re done! Waiting for {opp?.name || "your opponent"} to finish…</T>
      </View>
    );
  } else if (d.status === "finished") {
    const won = d.winner === d.you, tie = d.winner === "tie";
    const mine = me?.answers || [];
    body = (
      <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md }} testID="duel-result">
        <Animated.View entering={reduced || p.review ? undefined : ZoomIn.duration(300)}>
          <Card style={{ alignItems: "center", gap: space.sm, backgroundColor: colors.surfaceInverse, borderColor: colors.surfaceInverse }}>
            <Art kind={won ? "trophy" : "friends"} size={88} testID="duel-result-art" />
            <T w="heavy" size={26} color={colors.onSurfaceInverse} testID="duel-outcome">{won ? "You won!" : tie ? "It’s a tie" : "Good fight!"}</T>
            <T size={13} color={colors.custom_whiteA70}>{me?.name} {me?.score} · {opp?.score} {opp?.name}</T>
            {d.tie_break ? <T size={12} color={colors.custom_whiteA70}>Equal score — decided on total answer time</T> : null}
            <T size={11} color={colors.custom_whiteA70}>Practice duel · doesn’t change marks, ranks or the series streak</T>
            {d.finished_at ? <T testID="duel-finished-at" size={12} color={colors.muted}>{new Date(d.finished_at).toLocaleString()}</T> : null}
          </Card>
        </Animated.View>
        <RewardPanel reward={d.reward} title={p.review ? "Match rewards" : won ? "A well-earned victory" : tie ? "What a close match!" : "Every round makes you sharper"} testID="duel-reward" historical={!!p.review} />
        <Button testID="duel-rematch" icon="sword-cross" label="New random duel" color={colors.custom_amber} onPress={() => router.replace({ pathname: "/rapid/duel", params: { mode: "random", exam: d.exam, subject: d.subject, chapter: d.chapter || "", r: uuid() } })} />
        <Button testID="duel-invite-friend" kind="secondary" icon="whatsapp" label="Challenge a WhatsApp friend" onPress={() => router.replace({ pathname: "/rapid/duel", params: { mode: "invite", exam: d.exam, subject: d.subject, chapter: d.chapter || "", r: uuid() } })} />
        <Button testID="duel-done" kind="ghost" label="Done" onPress={() => router.back()} />
        <Button testID="duel-toggle-misses" kind="secondary" icon="book-open-outline" label={reviewMisses ? "Hide card review" : "Review your missed cards"} onPress={() => setReviewMisses(!reviewMisses)} />
        {reviewMisses ? d.cards.map((c: any, k: number) => {
          const a = mine[k];
          if (a && a.outcome === "correct") return null;
          return (
            <Card key={c.id} style={{ gap: 4 }} testID={"duel-review-" + k}>
              <RapidText text={`${k + 1}. ${c.prompt}`} size={15} testID={`duel-review-prompt-${k}`} />
              <BiologyDiagram diagram={c.diagram} testID={`duel-review-diagram-${k}`} />
              {c.formula ? <RapidText text={c.formula} size={17} testID={`duel-review-formula-${k}`} /> : null}
              <T size={12} color={colors.error}>{!a ? "Not reached" : a.outcome === "incorrect" ? `You chose: ${c.options[a.choice]}` : a.outcome === "timed_out" ? "Timed out" : "Skipped"}</T>
              <T size={12} w="bold" color={colors.success}>Correct: {c.options[c.answer]}</T>
              {c.explain ? <T size={11} color={colors.muted}>{c.explain}</T> : null}
            </Card>
          );
        }) : null}
      </ScrollView>
    );
  }

  return (
    <View testID="duel-screen" style={{ flex: 1, backgroundColor: colors.custom_gameBg, paddingTop: insets.top + space.sm, paddingBottom: insets.bottom }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: space.lg, minHeight: 52 }}>
        <Press testID="duel-exit-button" onPress={() => (d?.status === "ready" && started ? setExit(true) : leave())} accessibilityLabel="Leave duel" style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}>
          <Icon name="close" size={22} color={colors.onSurface} />
        </Press>
        <View style={{ flex: 1 }}>
          <T testID="duel-exam-group" w="heavy" size={12} color={colors.brandText}>{d?.exam || p.exam || "JEE"} DUEL · {(d?.subject || p.subject || "").toUpperCase()}</T>
          <T w="heavy" size={16} color={colors.onSurfaceInverse}>{d?.chapter || "Mixed chapters"}</T>
        </View>
        <Icon name="sword-cross" size={24} color={colors.custom_neonAmber} />
      </View>
      {body}
      {d?.status === "ready" && !started && intro !== d.id ? <EntryShow me={me} opp={opp} onDone={() => setIntro(d.id)} testID="duel-entry-show" /> : null}
      <Sheet visible={exit} onClose={() => setExit(false)} testID="duel-exit-sheet">
        <T w="heavy" size={19}>Leave the duel?</T>
        <T size={13} color={colors.muted}>Cards you don’t answer score 0. Your opponent keeps playing.</T>
        <Button testID="duel-exit-confirm" kind="danger" label="Leave duel" onPress={() => { if (d?.id) rf(`/duels/${d.id}/forfeit`, uid, { method: "POST", body: {} }).catch(() => {}); router.back(); }} />
        <Button testID="duel-exit-stay" label="Keep playing" onPress={() => setExit(false)} />
      </Sheet>
    </View>
  );
}

function Side({ p, right, total }: { p: any; right?: boolean; total: number }) {
  const reduced = useReducedMotion();
  return (
    <View style={{ flex: 1, gap: 4, alignItems: right ? "flex-end" : "flex-start" }}>
      <View style={{ flexDirection: right ? "row-reverse" : "row", alignItems: "center", gap: 6 }}>
        <Avatar icon={p?.avatar} frame={p?.frame} size={34} />
        <View style={{ flexShrink: 1, alignItems: right ? "flex-end" : "flex-start" }}>
          <T w="heavy" size={12} color={colors.onSurfaceInverse} numberOfLines={1}>{p?.you ? "You" : p?.name || "Waiting…"}</T>
          {p?.bot ? <T testID="duel-practice-rival-label" size={10} color={colors.custom_neonAmber}>Practice rival</T> : null}
        </View>
      </View>
      <Animated.View key={p?.score ?? 0} entering={reduced ? undefined : ZoomIn.duration(220)}>
        <T w="heavy" size={30} color={right ? colors.custom_neonAmber : colors.custom_neonCyan} testID={right ? "duel-opp-score" : "duel-my-score"}>{p?.score ?? 0}</T>
      </Animated.View>
      <View style={{ height: 6, width: "100%", borderRadius: 3, backgroundColor: colors.custom_gameLine, overflow: "hidden", alignItems: right ? "flex-end" : "flex-start" }}>
        <View style={{ width: `${((p?.answered || 0) / total) * 100}%`, height: "100%", backgroundColor: right ? colors.custom_neonRed : colors.custom_neonCyan }} />
      </View>
      <T size={10} color={colors.custom_gameMuted}>{p?.answered || 0}/{total} cards</T>
    </View>
  );
}

function VersusRow({ me, opp, tint, total }: { me: any; opp: any; tint: string; total: number }) {
  const lead = (me?.score ?? 0) - (opp?.score ?? 0);
  return (
    <View testID="duel-versus" style={{ alignSelf: "stretch", gap: 6 }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, padding: space.md, borderRadius: radius.lg, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_gameLine }}>
        <Side p={me} total={total} />
        <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: colors.custom_neonAmber, alignItems: "center", justifyContent: "center" }}>
          <T w="heavy" size={14} color={colors.custom_gameBg}>VS</T>
        </View>
        <Side p={opp} right total={total} />
      </View>
      {opp && !opp.forfeit ? <T w="heavy" size={12} testID="duel-lead" color={lead > 0 ? colors.custom_neonGreen : lead < 0 ? colors.custom_neonRed : colors.custom_neonAmber} style={{ textAlign: "center" }}>
        {lead > 0 ? `🔥 You lead by ${lead}! Keep it up` : lead < 0 ? `Behind by ${-lead} — push harder!` : "Neck and neck!"}
      </T> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  feedback: { gap: 8 },
  questionCard: { backgroundColor: colors.custom_reading, borderRadius: 26, padding: 20, gap: 18, borderWidth: 1, shadowColor: colors.custom_gameBg, shadowOpacity: 0.3, shadowRadius: 16, elevation: 4 },
  formula: { padding: 14, backgroundColor: colors.surface, borderRadius: 14 }, optionText: { flex: 1, paddingVertical: 12 },
  playScroll: { flex: 1 },
  playContent: { paddingHorizontal: space.lg, paddingBottom: space.md },
});

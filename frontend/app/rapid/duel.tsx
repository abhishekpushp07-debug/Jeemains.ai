import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Linking, ScrollView, Share, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as Clipboard from "expo-clipboard";
import Animated, { FadeIn, ZoomIn } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { rf, uuid } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { Button, Card, ErrorBox, Icon, Press, Sheet, T, tap } from "@/src/components/ui";
import { Ring } from "@/src/components/Ring";
import { RewardPanel } from "@/src/components/game";
import { colors, radius, space, subjectColor } from "@/src/theme";

const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());
const LIMIT = 20000;

export function playerName(phone?: string) {
  return phone ? "Player ··" + phone.slice(-4) : "Player";
}

function inviteText(code: string, subject: string) {
  return `⚡ Rapid Fire duel on JEELIVE.AI! ${subject} · 30 formula cards · 20 s each.\nJoin with code: ${code}\nOpen JEELIVE.AI → Rapid Fire → Join with code. Free for everyone: https://jeelive.ai`;
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
  const p = useLocalSearchParams<{ mode: "random" | "invite" | "join"; subject?: string; chapter?: string; code?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const uid = user?.id || "";
  const name = playerName(user?.phone);
  const [d, setD] = useState<any>(null);
  const [error, setError] = useState("");
  const [idx, setIdx] = useState(0);
  const [choice, setChoice] = useState<number | null>(null);
  const [fb, setFb] = useState<any>(null);
  const [left, setLeft] = useState(LIMIT);
  const [now, setNow] = useState(0);
  const [exit, setExit] = useState(false);
  const [copied, setCopied] = useState(false);
  const [n, setN] = useState(0);
  const reqId = useRef(uuid());
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
    setError("");
    const run = p.mode === "join"
      ? rf("/duels/join", uid, { method: "POST", body: { code: p.code || "", name } })
      : rf("/duels", uid, { method: "POST", body: { subject: p.subject || "Physics", chapter: p.chapter || null, mode: p.mode, name, request_id: reqId.current } });
    run.then((v) => alive && apply(v)).catch((e) => alive && setError(e.message));
    return () => { alive = false; };
  }, [p.mode, p.code, p.subject, p.chapter, uid, name, apply, n]);

  // Poll for opponent / progress (light: one small GET every 1.5 s, stops when finished).
  useEffect(() => {
    if (!d?.id || d.status === "finished" || d.status === "cancelled" || d.status === "expired") return;
    const iv = setInterval(() => {
      rf(`/duels/${d.id}`, uid).then(apply).catch(() => {});
    }, 1500 + Math.random() * 300);
    return () => clearInterval(iv);
  }, [d?.id, d?.status, uid, apply]);

  useEffect(() => {
    const iv = setInterval(() => setNow(serverNow()), 250);
    return () => clearInterval(iv);
  }, []);

  const me = d?.players?.find((x: any) => x.you);
  const opp = d?.players?.find((x: any) => !x.you);
  const started = d?.status === "ready" && d.start_at && now >= d.start_at;
  const total = d?.total || 30;
  const card = d?.cards?.[idx];

  useEffect(() => {
    if (me && me.answered > idx) setIdx(me.answered);
  }, [me?.answered]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!started || !card) return;
    startedAt.current = mono();
    setChoice(null);
    setFb(null);
    setLeft(LIMIT);
  }, [started, card?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback(async (outcome: "answer" | "skipped" | "timed_out", c: number | null) => {
    if (!d || sending.current || !card) return;
    sending.current = true;
    const ms = Math.min(LIMIT, Math.round(mono() - startedAt.current));
    try {
      const r = await rf(`/duels/${d.id}/answer`, uid, { method: "POST", body: { index: idx, choice: c, outcome, ms } });
      setFb(r);
      setTimeout(() => setIdx((i) => Math.max(i, r.index + 1)), outcome === "answer" ? 1100 : 600);
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
      setLeft(Math.max(0, l));
      if (l <= 0) {
        setChoice(-1);
        send("timed_out", null);
      }
    }, 100);
    return () => clearInterval(iv);
  }, [started, card?.id, choice, fb, send]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (d?.status === "finished") invalidate(`u.${uid}.duels`);
  }, [d?.status, uid]);

  function leave() {
    if (d?.status === "waiting") rf(`/duels/${d.id}/cancel`, uid, { method: "POST", body: {} }).catch(() => {});
    router.back();
  }
  const tint = subjectColor(d?.subject || p.subject);
  const waitedS = d?.status === "waiting" ? Math.max(0, Math.floor(now - (d.server_now - 0))) : 0;
  void waitedS;

  let body: React.ReactNode = null;
  if (!d) {
    body = error ? <View style={{ padding: space.lg, gap: space.md }}><ErrorBox error={error} retry={() => setN((x) => x + 1)} testID="duel-error" /><Button testID="duel-back" kind="secondary" label="Back" onPress={() => router.back()} /></View>
      : <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.md }}><ActivityIndicator color={tint} size="large" /><T w="bold" color={colors.onSurfaceInverse}>{p.mode === "join" ? "Joining duel…" : "Setting up your duel…"}</T></View>;
  } else if (d.status === "waiting" || d.status === "expired" || d.status === "cancelled") {
    const invite = d.mode === "invite";
    body = (
      <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.lg }} testID="duel-waiting">
        <Card style={{ alignItems: "center", gap: space.md, paddingVertical: space.xl }}>
          {d.status === "waiting" ? <ActivityIndicator size="large" color={tint} /> : <Icon name="account-clock-outline" size={44} color={colors.muted} />}
          <T w="heavy" size={20} style={{ textAlign: "center" }}>{d.status !== "waiting" ? "No opponent joined" : invite ? "Waiting for your friend…" : `Finding a ${d.subject} opponent…`}</T>
          <T size={13} color={colors.muted} style={{ textAlign: "center" }}>{d.status !== "waiting" ? "Nobody was free for this subject right now. Invite a friend or play solo." : invite ? "Share the code. The duel starts the moment they join." : "Matching you with a random student on the same subject. We never fake an opponent."}</T>
        </Card>
        {invite && d.status === "waiting" ? (
          <Card style={{ alignItems: "center", gap: space.md }} testID="duel-invite-card">
            <T w="bold" size={11} color={colors.muted} style={{ letterSpacing: 1 }}>DUEL CODE</T>
            <T w="heavy" size={38} style={{ letterSpacing: 6 }} testID="duel-code">{d.code}</T>
            <Button testID="duel-share-whatsapp" label="Send on WhatsApp" icon="whatsapp" color={colors.success} onPress={() => shareOnWhatsApp(d.code, d.subject)} style={{ alignSelf: "stretch" }} />
            <Button testID="duel-copy-code" kind="secondary" icon={copied ? "check" : "content-copy"} label={copied ? "Copied" : "Copy code"} onPress={async () => { await Clipboard.setStringAsync(d.code); setCopied(true); }} style={{ alignSelf: "stretch" }} />
          </Card>
        ) : null}
        {!invite || d.status !== "waiting" ? (
          <Button testID="duel-invite-instead" kind="secondary" icon="whatsapp" label="Invite a WhatsApp friend instead" onPress={() => { leave(); router.push({ pathname: "/rapid/duel", params: { mode: "invite", subject: d.subject, chapter: d.chapter || "" } }); }} />
        ) : null}
        <Button testID="duel-play-solo" kind="ghost" label="Play solo instead" onPress={() => { leave(); router.push({ pathname: "/rapid/session", params: { subject: d.subject, chapter: d.chapter || "" } }); }} />
      </ScrollView>
    );
  } else if (d.status === "ready" && !started) {
    const c = Math.max(1, Math.ceil(d.start_at - now));
    body = (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: space.lg }} testID="duel-countdown">
        <VersusRow me={me} opp={opp} tint={tint} total={total} />
        <Animated.View key={c} entering={ZoomIn.duration(250)}><T w="heavy" size={88} color={colors.custom_neonAmber}>{c}</T></Animated.View>
        <T size={13} color={colors.custom_gameMuted}>Same 30 cards for both · 20 s each · +1 per correct</T>
      </View>
    );
  } else if (d.status === "ready" && card) {
    const locked = choice !== null;
    body = (
      <View style={{ flex: 1, paddingHorizontal: space.lg }} testID="duel-play">
        <VersusRow me={me} opp={opp} tint={tint} total={total} />
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginVertical: space.sm }}>
          <T w="heavy" size={15} color={colors.onSurfaceInverse} testID="duel-card-counter">Card {idx + 1} / {total}</T>
          <Ring light left={left} color={tint} />
        </View>
        <Animated.View key={card.id} entering={FadeIn.duration(160)} testID="duel-card" style={{ backgroundColor: colors.custom_reading, borderRadius: radius.lg, padding: space.xl, gap: space.md, borderWidth: 1, borderColor: colors.border, shadowColor: colors.surfaceInverse, shadowOpacity: 0.1, shadowRadius: 16, elevation: 5 }}>
          <T w="bold" size={11} color={tint}>{card.chapter}</T>
          <T w="heavy" size={18} color={colors.custom_onReading}>{card.prompt}</T>
          {card.formula ? <View style={{ padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface }}><T w="heavy" size={19} color={colors.custom_series} style={{ textAlign: "center" }}>{card.formula}</T></View> : null}
          {card.options.map((o: string, k: number) => {
            const isAns = fb && k === fb.answer, picked = k === choice;
            const bg = isAns ? colors.custom_successSoft : fb && picked ? colors.custom_errorSoft : picked ? colors.custom_infoSoft : colors.surfaceSecondary;
            const bd = isAns ? colors.success : fb && picked ? colors.error : picked ? colors.brandPrimary : colors.border;
            return (
              <Press key={k} testID={"duel-option-" + k} disabled={locked} haptic={false} onPress={() => { tap("medium"); setChoice(k); send("answer", k); }} accessibilityLabel={o}
                style={{ minHeight: 50, borderRadius: radius.md, borderWidth: 2, borderColor: bd, backgroundColor: bg, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm }}>
                <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
                <T w="bold" size={15} style={{ flex: 1 }} color={colors.custom_onReading}>{o}</T>
                {isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : fb && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
              </Press>
            );
          })}
          {fb ? <T w="heavy" size={14} testID="duel-feedback" color={fb.outcome === "correct" ? colors.success : fb.outcome === "incorrect" ? colors.error : colors.warning}>{fb.outcome === "correct" ? "✓ Correct +1" : fb.outcome === "incorrect" ? "✗ Incorrect" : fb.outcome === "timed_out" ? "⏱ Timed out" : "↷ Skipped"}{fb.explain ? " · " + fb.explain : ""}</T> : null}
        </Animated.View>
        <View style={{ flexDirection: "row", gap: space.sm, paddingVertical: space.md }}>
          <Button testID="duel-skip" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={() => { setChoice(-1); send("skipped", null); }} style={{ flex: 1 }} />
        </View>
        <ErrorBox error={error} />
      </View>
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
        <Animated.View entering={ZoomIn.duration(300)}>
          <Card style={{ alignItems: "center", gap: space.sm, backgroundColor: colors.surfaceInverse, borderColor: colors.surfaceInverse }}>
            <Icon name={won ? "trophy" : tie ? "handshake-outline" : "arm-flex-outline"} size={44} color={won ? colors.custom_examComedkGold : colors.onSurfaceInverse} />
            <T w="heavy" size={26} color={colors.onSurfaceInverse} testID="duel-outcome">{won ? "You won!" : tie ? "It’s a tie" : "Good fight!"}</T>
            <T size={13} color={colors.custom_whiteA70}>{me?.name} {me?.score} · {opp?.score} {opp?.name}</T>
            {d.tie_break ? <T size={12} color={colors.custom_whiteA70}>Equal score — decided on total answer time</T> : null}
            <T size={11} color={colors.custom_whiteA70}>Practice duel · doesn’t change marks, ranks or the series streak</T>
          </Card>
        </Animated.View>
        <RewardPanel reward={d.reward} title={won ? "Victory! Champion’s prize" : tie ? "Draw! Shared spoils" : "Battle reward earned"} testID="duel-reward" />
        <T w="heavy" size={16} color={colors.onSurfaceInverse}>Review your misses</T>
        {d.cards.map((c: any, k: number) => {
          const a = mine[k];
          if (a && a.outcome === "correct") return null;
          return (
            <Card key={c.id} style={{ gap: 4 }} testID={"duel-review-" + k}>
              <T w="bold" size={12}>{k + 1}. {c.prompt}</T>
              {c.formula ? <T w="heavy" size={14} color={colors.custom_series}>{c.formula}</T> : null}
              <T size={12} color={colors.error}>{!a ? "Not reached" : a.outcome === "incorrect" ? `You chose: ${c.options[a.choice]}` : a.outcome === "timed_out" ? "Timed out" : "Skipped"}</T>
              <T size={12} w="bold" color={colors.success}>Correct: {c.options[c.answer]}</T>
              {c.explain ? <T size={11} color={colors.muted}>{c.explain}</T> : null}
            </Card>
          );
        })}
        <Button testID="duel-rematch" icon="sword-cross" label="New random duel" color={colors.custom_amber} onPress={() => router.replace({ pathname: "/rapid/duel", params: { mode: "random", subject: d.subject, chapter: d.chapter || "", r: uuid() } })} />
        <Button testID="duel-invite-friend" kind="secondary" icon="whatsapp" label="Challenge a WhatsApp friend" onPress={() => router.replace({ pathname: "/rapid/duel", params: { mode: "invite", subject: d.subject, chapter: d.chapter || "", r: uuid() } })} />
        <Button testID="duel-done" kind="ghost" label="Done" onPress={() => router.back()} />
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
          <T w="heavy" size={12} color={tint}>RAPID FIRE DUEL · {(d?.subject || p.subject || "").toUpperCase()}</T>
          <T w="heavy" size={16} color={colors.onSurfaceInverse}>{d?.chapter || "Mixed chapters"}</T>
        </View>
        <Icon name="sword-cross" size={24} color={colors.custom_amber} />
      </View>
      {body}
      <Sheet visible={exit} onClose={() => setExit(false)} testID="duel-exit-sheet">
        <T w="heavy" size={19}>Leave the duel?</T>
        <T size={13} color={colors.muted}>Cards you don’t answer score 0. Your opponent keeps playing.</T>
        <Button testID="duel-exit-confirm" kind="danger" label="Leave duel" onPress={() => { if (d?.id) rf(`/duels/${d.id}/forfeit`, uid, { method: "POST", body: {} }).catch(() => {}); router.back(); }} />
        <Button testID="duel-exit-stay" label="Keep playing" onPress={() => setExit(false)} />
      </Sheet>
    </View>
  );
}

function VersusRow({ me, opp, tint, total }: { me: any; opp: any; tint: string; total: number }) {
  const Side = ({ p, right }: { p: any; right?: boolean }) => (
    <View style={{ flex: 1, gap: 4, alignItems: right ? "flex-end" : "flex-start" }}>
      <T w="heavy" size={13} numberOfLines={1}>{p?.name || "Waiting…"}</T>
      <T w="heavy" size={22} color={right ? colors.custom_examJee : tint}>{p?.score ?? 0}</T>
      <View style={{ height: 5, width: "100%", borderRadius: 3, backgroundColor: colors.border, overflow: "hidden", alignItems: right ? "flex-end" : "flex-start" }}>
        <View style={{ width: `${((p?.answered || 0) / total) * 100}%`, height: "100%", backgroundColor: right ? colors.custom_examJee : tint }} />
      </View>
      <T size={10} color={colors.muted}>{p?.answered || 0}/{total} cards</T>
    </View>
  );
  return (
    <View testID="duel-versus" style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: radius.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, alignSelf: "stretch" }}>
      <Side p={me} />
      <T w="heavy" size={14} color={colors.custom_amber}>VS</T>
      <Side p={opp} right />
    </View>
  );
}

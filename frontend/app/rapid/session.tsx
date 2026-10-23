import React, { useCallback, useEffect, useRef, useState } from "react";
import { AppState, ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, { FadeIn, runOnJS, useAnimatedStyle, useReducedMotion, useSharedValue, withSpring, withTiming } from "react-native-reanimated";
import { Ring } from "@/src/components/Ring";
import { useAuth } from "@/src/auth";
import { rf, uuid } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { Button, Card, Empty, ErrorBox, Icon, Press, Sheet, Skeleton, Stat, T, tap } from "@/src/components/ui";
import { colors, radius, space, subjectColor } from "@/src/theme";

const LIMIT = 20000;
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());
type RCard = { id: string; subject: string; chapter: string; topic: string; prompt: string; formula: string; options: string[]; answer: number; explain: string };
type Res = { card_id: string; outcome: "correct" | "incorrect" | "skipped" | "timed_out"; choice: number | null; ms: number };

function Summary({ s, cards, onRepeat, onAgain, onExit }: { s: any; cards: RCard[]; onRepeat: (ids: string[]) => void; onAgain: () => void; onExit: () => void }) {
  const [review, setReview] = useState(false);
  const sum = s.summary;
  const byId = Object.fromEntries(cards.map((c) => [c.id, c]));
  const missed = (s.results || []).filter((r: any) => r.outcome !== "correct");
  return (
    <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md }} testID="rf-summary">
      <Card style={{ alignItems: "center", gap: 4, backgroundColor: colors.surfaceInverse, borderColor: colors.surfaceInverse }}>
        <T w="bold" size={11} color={colors.custom_whiteA70} style={{ letterSpacing: 1 }}>SESSION SCORE</T>
        <T w="heavy" size={44} color={colors.onSurfaceInverse} testID="rf-summary-score">{sum.score}<T w="semibold" size={22} color={colors.custom_whiteA70}> / {sum.total}</T></T>
        <T size={13} color={colors.custom_whiteA70}>Answered accuracy {sum.accuracy != null ? sum.accuracy + "%" : "—"} ({sum.correct}/{sum.answered} answered)</T>
      </Card>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Stat testID="rf-sum-correct" label="Correct" value={sum.correct} color={colors.success} />
        <Stat testID="rf-sum-incorrect" label="Incorrect" value={sum.incorrect} color={colors.error} />
      </View>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        <Stat testID="rf-sum-skipped" label="Skipped" value={sum.skipped} />
        <Stat testID="rf-sum-timeout" label="Timed out" value={sum.timed_out} color={colors.warning} />
      </View>
      {sum.revise_topics?.length ? (
        <Card style={{ gap: 4 }} testID="rf-revise-topics">
          <T w="heavy" size={15}>Worth revising (from this session)</T>
          {sum.revise_topics.map((t: string) => <T key={t} size={13}>• {t}</T>)}
          <T size={10} color={colors.muted}>Based on just these cards — not a diagnosis of your ability.</T>
        </Card>
      ) : null}
      {missed.length ? <Button testID="rf-review-missed" kind="secondary" icon="eye-outline" label={review ? "Hide review" : `Review ${missed.length} missed card${missed.length > 1 ? "s" : ""}`} onPress={() => setReview(!review)} /> : null}
      {review ? missed.map((m: any) => {
        const c = byId[m.card_id];
        if (!c) return null;
        return (
          <Card key={m.card_id} testID={"rf-review-" + m.card_id} style={{ gap: 6 }}>
            <T w="bold" size={11} color={subjectColor(c.subject)}>{c.chapter}</T>
            <T w="bold" size={15}>{c.prompt}</T>
            {c.formula ? <T w="heavy" size={16} color={colors.custom_series}>{c.formula}</T> : null}
            <T size={13} color={colors.error}>{m.outcome === "timed_out" ? "⏱ Timed out" : m.outcome === "skipped" ? "↷ Skipped" : `✗ You chose: ${c.options[m.choice]}`}</T>
            <T size={13} w="bold" color={colors.success}>✓ Correct: {c.options[c.answer]}</T>
            {c.explain ? <T size={12} color={colors.muted}>{c.explain}</T> : null}
          </Card>
        );
      }) : null}
      {missed.length ? <Button testID="rf-repeat-missed" icon="repeat" label="Repeat missed as a fresh session" color={colors.custom_amber} onPress={() => onRepeat(missed.map((m: any) => m.card_id))} /> : null}
      <Button testID="rf-start-another" kind="secondary" icon="lightning-bolt" label="Start another session" onPress={onAgain} />
      <Button testID="rf-done" kind="ghost" label="Done" onPress={onExit} />
    </ScrollView>
  );
}

export default function RapidSession() {
  const p = useLocalSearchParams<{ subject?: string; chapter?: string; ids?: string; review?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const reduced = useReducedMotion();
  const [session, setSession] = useState<any>(null);
  const [cards, setCards] = useState<RCard[]>([]);
  const [error, setError] = useState("");
  const [empty, setEmpty] = useState(false);
  const [i, setI] = useState(0);
  const [choice, setChoice] = useState<number | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const [left, setLeft] = useState(LIMIT);
  const [done, setDone] = useState<any>(null);
  const [exit, setExit] = useState(false);
  const [n, setN] = useState(0);
  const results = useRef<Res[]>([]);
  const startedAt = useRef(0);
  const reqId = useRef(uuid());
  const x = useSharedValue(0);
  const uid = user?.id || "";
  const card = cards[i];
  const locked = choice !== null || timedOut;

  useEffect(() => {
    let alive = true;
    setError("");
    const run = p.review
      ? rf(`/sessions/${p.review}`, uid).then((s) => { if (!alive) return; setCards(s.cards); if (s.status === "completed") setDone(s); else setSession(s); })
      : rf("/sessions", uid, { method: "POST", body: { subject: p.subject || "Physics", chapter: p.chapter || null, count: 30, request_id: reqId.current, ...(p.ids ? { card_ids: p.ids.split(",") } : {}) } })
          .then((s) => { if (!alive) return; setSession(s); setCards(s.cards); });
    run.catch((e) => { if (!alive) return; if (e.status === 404) setEmpty(true); else setError(e.message); });
    return () => { alive = false; };
  }, [p.review, p.subject, p.chapter, p.ids, uid, n]);

  // Timer starts only when the card is visible; resets per card.
  useEffect(() => {
    if (!card || done) return;
    startedAt.current = mono();
    setLeft(LIMIT);
    setChoice(null);
    setTimedOut(false);
    x.value = 0;
  }, [card?.id, done]); // eslint-disable-line react-hooks/exhaustive-deps

  const finish = useCallback(async () => {
    try {
      const s = await rf(`/sessions/${session.id}/complete`, uid, { method: "POST", body: { results: results.current } });
      invalidate(`u.${uid}.rfhist`);
      setDone(s);
    } catch (e: any) { setError(e.message + " Your answers are kept — tap Retry."); }
  }, [session, uid]);

  const advance = useCallback(() => {
    if (i + 1 >= cards.length) finish();
    else setI(i + 1);
  }, [i, cards.length, finish]);

  const record = (r: Res) => { results.current = [...results.current.filter((y) => y.card_id !== r.card_id), r]; };

  useEffect(() => {
    if (!card || locked || done) return;
    const iv = setInterval(() => {
      const l = LIMIT - (mono() - startedAt.current);
      setLeft(Math.max(0, l));
      if (l <= 0) {
        // Only the current visible card expires; future cards are never consumed in background.
        record({ card_id: card.id, outcome: "timed_out", choice: null, ms: LIMIT });
        setTimedOut(true);
      }
    }, 100);
    const sub = AppState.addEventListener("change", () => {});
    return () => { clearInterval(iv); sub.remove(); };
  }, [card?.id, locked, done]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!timedOut) return;
    const t = setTimeout(advance, 1400);
    return () => clearTimeout(t);
  }, [timedOut, advance]);

  function answer(k: number) {
    if (locked || !card) return;
    tap("medium");
    setChoice(k);
    record({ card_id: card.id, outcome: k === card.answer ? "correct" : "incorrect", choice: k, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
  }
  function skip() {
    if (locked || !card) return;
    tap();
    record({ card_id: card.id, outcome: "skipped", choice: null, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
    fly(-1);
  }
  function next() {
    if (choice === null) return;
    tap();
    fly(1);
  }
  function fly(dir: number) {
    if (reduced) { advance(); return; }
    x.value = withTiming(dir * 500, { duration: 180 }, (f) => { if (f) runOnJS(advance)(); });
  }

  const pan = Gesture.Pan().activeOffsetX([-15, 15]).onUpdate((e) => { x.value = e.translationX; }).onEnd((e) => {
    if (e.translationX > 110 && choice !== null) runOnJS(next)();
    else if (e.translationX < -110 && choice === null && !timedOut) runOnJS(skip)();
    else x.value = withSpring(0);
  });
  const cardStyle = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }, { rotate: `${x.value / 25}deg` }] }));

  const tint = subjectColor(card?.subject || p.subject);
  const onAgain = () => router.replace({ pathname: "/rapid/session", params: { subject: p.subject || cards[0]?.subject || "Physics", chapter: p.chapter || "", r: uuid() } });

  return (
    <View testID="rf-session-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm, paddingBottom: insets.bottom }}>
      <View style={{ flexDirection: "row", alignItems: "center", paddingHorizontal: space.lg, gap: space.md, minHeight: 56 }}>
        <Press testID="rf-exit-button" onPress={() => (done || empty || error && !session ? router.back() : setExit(true))} accessibilityLabel="Exit session" style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}>
          <Icon name="close" size={22} color={colors.onSurface} />
        </Press>
        <View style={{ flex: 1 }}>
          <T w="heavy" size={12} color={tint} numberOfLines={1}>{card ? `${card.subject} · ${card.chapter}` : "Rapid Fire"}</T>
          {card && !done ? <T w="heavy" size={16} testID="rf-card-counter">Card {i + 1} of {cards.length}</T> : <T w="heavy" size={16}>{done ? "Session complete" : "Loading cards…"}</T>}
        </View>
        {card && !done ? <Ring left={locked ? (timedOut ? 0 : left) : left} color={tint} /> : null}
      </View>
      {card && !done ? (
        <View style={{ flexDirection: "row", gap: 2, paddingHorizontal: space.lg, marginBottom: space.md }}>
          {cards.map((c, k) => <View key={c.id} style={{ flex: 1, height: 4, borderRadius: 1, backgroundColor: k < i ? tint : k === i ? colors.onSurface : colors.border }} />)}
        </View>
      ) : null}

      {error ? <View style={{ padding: space.lg }}><ErrorBox error={error} retry={() => (session ? finish() : setN((v) => v + 1))} testID="rf-error" /></View> : null}
      {empty ? <View style={{ padding: space.lg }}><Card testID="rf-empty"><Empty icon="cards-outline" title="No reviewed cards here yet" body="Only short formula and concept cards appear in Rapid Fire. Try mixed mode or another chapter." action={<Button testID="rf-empty-back" kind="secondary" label="Choose again" onPress={() => router.back()} />} /></Card></View> : null}
      {!card && !error && !empty && !done ? <View style={{ padding: space.lg }}><Skeleton h={380} /></View> : null}

      {done ? <Summary s={done} cards={cards} onExit={() => router.back()} onAgain={onAgain} onRepeat={(ids) => router.replace({ pathname: "/rapid/session", params: { subject: cards[0]?.subject, ids: ids.join(",") } })} /> : card ? (
        <View style={{ flex: 1, paddingHorizontal: space.lg }}>
          <View style={{ flex: 1, justifyContent: "center" }}>
            {cards[i + 1] ? <View pointerEvents="none" style={{ position: "absolute", left: 14, right: 14, top: 30, bottom: 6, borderRadius: radius.lg, backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border, transform: [{ scale: 0.95 }], opacity: 0.8 }} /> : null}
            <GestureDetector gesture={pan}>
              <Animated.View key={card.id} entering={reduced ? undefined : FadeIn.duration(180)} testID="rf-card" style={[{ backgroundColor: colors.custom_reading, borderRadius: radius.lg, padding: space.xl, gap: space.md, borderWidth: 1, borderColor: colors.border, shadowColor: colors.surfaceInverse, shadowOpacity: 0.12, shadowRadius: 18, shadowOffset: { width: 0, height: 10 }, elevation: 6 }, cardStyle]}>
                <View style={{ height: 4, width: 48, borderRadius: 2, backgroundColor: tint }} />
                <T w="heavy" size={19} color={colors.custom_onReading} testID="rf-card-prompt">{card.prompt}</T>
                {card.formula ? <View style={{ padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface }}><T w="heavy" size={20} color={colors.custom_series} style={{ textAlign: "center" }} testID="rf-card-formula">{card.formula}</T></View> : null}
                <View style={{ gap: space.sm }}>
                  {card.options.map((o, k) => {
                    const isAns = k === card.answer, picked = k === choice;
                    const show = locked;
                    const bg = show && isAns ? colors.custom_successSoft : show && picked ? colors.custom_errorSoft : colors.surfaceSecondary;
                    const bd = show && isAns ? colors.success : show && picked ? colors.error : colors.border;
                    return (
                      <Press key={k} testID={"rf-option-" + k} disabled={locked} onPress={() => answer(k)} haptic={false} accessibilityLabel={`${o}${show && isAns ? ", correct answer" : show && picked ? ", your choice, incorrect" : ""}`}
                        style={{ minHeight: 52, borderRadius: radius.md, borderWidth: 2, borderColor: bd, backgroundColor: bg, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm }}>
                        <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
                        <T w="bold" size={15} style={{ flex: 1 }} color={colors.custom_onReading}>{o}</T>
                        {show && isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : show && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
                      </Press>
                    );
                  })}
                </View>
                {locked ? (
                  <View testID="rf-feedback" accessibilityLiveRegion="polite" style={{ gap: 2 }}>
                    <T w="heavy" size={15} color={timedOut ? colors.warning : choice === card.answer ? colors.success : colors.error}>{timedOut ? "⏱ Timed out" : choice === card.answer ? "✓ Correct" : "✗ Incorrect"}</T>
                    {card.explain ? <T size={13} color={colors.muted} numberOfLines={2}>{card.explain}</T> : null}
                  </View>
                ) : null}
              </Animated.View>
            </GestureDetector>
          </View>
          <View style={{ flexDirection: "row", gap: space.sm, paddingVertical: space.md }}>
            <Button testID="rf-skip-button" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={skip} style={{ flex: 1 }} />
            <Button testID="rf-next-button" icon="arrow-right" label={i + 1 >= cards.length ? "Finish" : "Next"} disabled={choice === null} onPress={next} color={colors.custom_amber} style={{ flex: 1.4 }} />
          </View>
          <T size={11} color={colors.muted} style={{ textAlign: "center", paddingBottom: space.sm }}>Tap an option to lock it · swipe right for next · swipe left to skip</T>
        </View>
      ) : null}

      <Sheet visible={exit} onClose={() => setExit(false)} testID="rf-exit-sheet">
        <T w="heavy" size={19}>Leave this session?</T>
        <T size={13} color={colors.muted}>Cards you haven’t seen won’t be counted. You can finish now to save what you’ve done.</T>
        <Button testID="rf-exit-finish" label="Finish & see summary" onPress={() => { setExit(false); finish(); }} color={colors.custom_amber} />
        <Button testID="rf-exit-discard" kind="secondary" label="Leave without saving" onPress={() => router.back()} />
        <Button testID="rf-exit-stay" kind="ghost" label="Keep going" onPress={() => setExit(false)} />
      </Sheet>
    </View>
  );
}

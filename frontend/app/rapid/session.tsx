import React, { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import Animated, { FadeIn, runOnJS, useAnimatedStyle, useReducedMotion, useSharedValue, withSpring, withTiming } from "react-native-reanimated";
import { CardClock } from "@/src/rapid/CardClock";
import { RapidDiagram as BiologyDiagram, RapidDiagramSpec as Diagram } from "@/src/rapid/Diagram";
import { RewardPanel } from "@/src/components/game";
import { useAuth } from "@/src/auth";
import { ApiError, rf, uuid } from "@/src/api/client";
import { bankCanDeal } from "@/src/offline/bank";
import { keepRound, summarise } from "@/src/offline/rounds";
import { invalidate } from "@/src/useCached";
import { Button, Card, Empty, ErrorBox, Icon, Press, Sheet, Skeleton, Stat, T, buzz, tap, withRapid } from "@/src/rapid/ui";
import { RapidText } from "@/src/rapid/RapidText";
import { playSfx } from "@/src/sfx";
import { GemColor } from "@/src/rapid/Art";
import { ArenaBg } from "@/src/rapid/arena";
import { CARD_COUNTS, CARD_SECONDS, decodePicks, isBitsat } from "@/src/rapid/scope";
import { ArenaWait, useArenaWait } from "@/src/rapid/ArenaWait";
import { DiamondsWon, GemFlare, StreakGem, gemAt } from "@/src/rapid/StreakGem";
import { rapidColors as colors, radius, space, rapidSubjectColor as subjectColor } from "@/src/theme";

const LIMIT = CARD_SECONDS * 1000;
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());
// The server was not heard at all: no line, or a line too slow (not an answer of its own, such as "the arena is full").
const noLine = (e: any) => !(e instanceof ApiError) || e.status === 0;
const SLOW_MS = 4000; // a fresh sprint the server has not dealt by then is dealt from the phone's own cards
type RCard = { id: string; exam?: string; subject: string; chapter: string; topic: string; prompt: string; formula: string; options: string[]; answer: number; explain: string; diagram?: Diagram };
type Res = { card_id: string; outcome: "correct" | "incorrect" | "skipped" | "timed_out"; choice: number | null; ms: number };

function Summary({ s, cards, onRepeat, onAgain, onExit, historical }: { s: any; cards: RCard[]; onRepeat: (ids: string[]) => void; onAgain: () => void; onExit: () => void; historical?: boolean }) {
  const [review, setReview] = useState(false);
  const sum = s.summary;
  const byId = Object.fromEntries(cards.map((c) => [c.id, c]));
  const missed = (s.results || []).filter((r: any) => r.outcome !== "correct");
  return (
    <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md }} testID="rf-summary">
      <RewardPanel reward={s.reward} historical={historical} title={!sum.answered ? "No cards answered" : sum.accuracy >= 80 && sum.answered >= 10 ? "What a run!" : "Sprint complete"} />
      {s.kept ? <T testID="rf-kept-note" w="bold" size={13} color={colors.custom_neonCyan}>Internet chala gaya, par aapke answers phone par rakhe hain. Line aate hi apne aap bhej diye jayenge; coins aur XP tab judenge.</T> : null}
      {s.mode === "fresh" ? <DiamondsWon reward={s.reward} /> : null}
      <T testID="rf-summary-exam" w="bold" size={12} color={colors.custom_neonCyan}>{s.mode !== "weak_topics" && cards.length && cards.every((c) => isBitsat(c.subject)) ? "BITSAT" : s.exam} · {s.mode === "weak_revision" ? "Weak chapter revision" : s.mode === "weak_topics" ? "Weak Topic Sprint" : "Solo Sprint"}</T>
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
            <T w="bold" size={11} color={colors.muted}>{c.chapter}</T>
            <RapidText testID={`rf-review-prompt-${c.id}`} text={c.prompt} size={16} />
            <BiologyDiagram diagram={c.diagram} testID={`rf-review-diagram-${c.id}`} />
            {c.formula ? <RapidText testID={`rf-review-formula-${c.id}`} text={c.formula} size={18} /> : null}
            <RapidText testID={`rf-review-chosen-${c.id}`} size={13} w="regular" color={colors.error} text={m.outcome === "timed_out" ? "⏱ Timed out" : m.outcome === "skipped" ? "↷ Skipped" : `✗ You chose: ${c.options[m.choice]}`} />
            <RapidText testID={`rf-review-correct-${c.id}`} size={13} w="bold" color={colors.success} text={`✓ Correct: ${c.options[c.answer]}`} />
            {c.explain ? <RapidText testID={`rf-review-explain-${c.id}`} size={12} w="regular" color={colors.muted} text={c.explain} /> : null}
          </Card>
        );
      }) : null}
      {missed.length ? <Button testID="rf-repeat-missed" icon="repeat" label="Repeat missed as a fresh session" color={colors.custom_amber} onPress={() => onRepeat(missed.map((m: any) => m.card_id))} /> : null}
      <Button testID="rf-start-another" kind="secondary" icon="lightning-bolt" label="Start another session" onPress={onAgain} />
      <Button testID="rf-done" kind="ghost" label="Done" onPress={onExit} />
    </ScrollView>
  );
}

function RapidSession() {
  const p = useLocalSearchParams();
  return <RapidSessionRound key={JSON.stringify([p.r, p.review, p.subject, p.chapter, p.picks, p.ids, p.exam, p.revision, p.weak, p.n])} />;
}

function RapidSessionRound() {
  const p = useLocalSearchParams<{ exam?: "JEE" | "NEET"; subject?: string; chapter?: string; picks?: string; ids?: string; review?: string; diagrams?: string; revision?: string; weak?: string; n?: string }>();
  const picks = decodePicks(p.picks);
  const size = (CARD_COUNTS as readonly number[]).includes(Number(p.n)) ? Number(p.n) : 30;
  const insets = useSafeAreaInsets();
  const narrow = useWindowDimensions().width < 360;
  const router = useRouter();
  const { user } = useAuth();
  const reduced = useReducedMotion();
  const [session, setSession] = useState<any>(null);
  const [cards, setCards] = useState<RCard[]>([]);
  const [error, setError] = useState(() => (p.exam && p.exam !== "JEE") || p.subject === "Biology" || p.diagrams === "1" ? "This practice is archived. Return to JEE Main Rapid Fire." : "");
  const [empty, setEmpty] = useState(false);
  const [i, setI] = useState(0);
  // The answer and the time-out belong to one card, so a new card can never show the last card's lock, not even for a frame.
  const [picked, setPicked] = useState<{ id: string; k: number } | null>(null);
  const [expired, setExpired] = useState("");
  const [done, setDone] = useState<any>(null);
  const [exit, setExit] = useState(false);
  const [n, setN] = useState(0);
  const results = useRef<Res[]>([]);
  const [combo, setCombo] = useState(0);
  const [flare, setFlare] = useState<GemColor | null>(null);
  const startedAt = useRef(0);
  const reqId = useRef(uuid());
  const seat = useArenaWait(() => setN((v) => v + 1));
  const scrollRef = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const x = useSharedValue(0);
  const uid = user?.id || "";
  // After a page reload (browser arena) there is no screen behind this one: leave to the lobby instead of doing nothing.
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"));
  const card = cards[i];
  const choice = picked && picked.id === card?.id ? picked.k : null;
  const timedOut = !!card && expired === card.id;
  const locked = choice !== null || timedOut;
  const fresh = session?.mode === "fresh";

  useEffect(() => {
    let alive = true;
    if (!uid) return; // wait for auth hydration (avoids a 401 POST on cold deep-link)
    if ((p.exam && p.exam !== "JEE") || p.subject === "Biology" || p.diagrams === "1") {
      return;
    }
    // A fresh sprint on the student's own picks can also be dealt from the cards this phone keeps (src/offline/bank.ts):
    // when the server is not heard (no line), or has not dealt in 4 seconds (a slow line), the sprint starts from there.
    const own = !p.review && !p.ids && p.revision !== "1" && p.weak !== "1" ? picks : null;
    const toPhone = async () => {
      if (!alive || !own || !(await bankCanDeal(own, size)) || !alive) return false;
      alive = false;
      router.replace({ pathname: "/offline/rapid", params: { picks: p.picks || "", n: String(size), r: uuid() } } as any);
      return true;
    };
    const slow = own ? setTimeout(() => { void toPhone(); }, SLOW_MS) : undefined;
    const run = p.review
      ? rf(`/sessions/${p.review}`, uid).then((s) => { if (!alive) return; setCards(s.cards); if (s.status === "completed") setDone(s); else setSession(s); })
      : rf("/sessions", uid, { method: "POST", body: { exam: "JEE", subject: picks?.[0].subject || p.subject || "Physics", chapter: picks ? null : p.chapter || null, count: p.revision === "1" || p.ids ? 30 : size, revision: p.revision === "1", weak_topics: p.weak === "1", request_id: reqId.current,
          ...(picks && !p.ids && p.revision !== "1" && p.weak !== "1" ? { picks } : {}), ...(p.ids ? { card_ids: p.ids.split(",") } : {}) } })
          .then((s) => { clearTimeout(slow); if (!alive) return; setSession(s); setCards(s.cards); });
    run.catch(async (e) => {
      clearTimeout(slow);
      if (!alive) return;
      if (e.status === 404) setEmpty(true);
      else if (noLine(e) && await toPhone()) return;
      else if (alive && !seat.hold(e)) setError(e.message);
    });
    return () => { alive = false; clearTimeout(slow); };
  }, [p.review, p.subject, p.chapter, p.picks, p.ids, p.exam, p.diagrams, p.revision, p.weak, uid, n]); // eslint-disable-line react-hooks/exhaustive-deps

  // The clock starts only when the card is visible. One light reset per card keeps native maths views mounted between cards.
  useEffect(() => {
    if (!card || done) return;
    startedAt.current = mono();
    scrollRef.current?.scrollTo({ y: 0, animated: false });
    x.set(0);
  }, [card?.id, done]); // eslint-disable-line react-hooks/exhaustive-deps

  const finish = useCallback(async () => {
    try {
      const s = await rf(`/sessions/${session.id}/complete`, uid, { method: "POST", body: { results: results.current } });
      invalidate(`u.${uid}.rfhist`);
      invalidate(`u.${uid}.rfprofile`);
      invalidate(`u.${uid}.rfshop`);
      invalidate(`u.${uid}.revision`);
      invalidate(`u.${uid}.rfweaktopics`);
      invalidate(`u.${uid}.rfboard`);
      setDone(s);
    } catch (e: any) {
      // The line dropped at the end: the answers stay on this phone and go up by themselves (src/offline/rounds.ts);
      // the result is marked here meanwhile, the same way the server marks it.
      if (noLine(e) && session?.id && cards.length) {
        await keepRound(uid, { request_id: reqId.current, session: session.id, card_ids: cards.map((c) => c.id), results: results.current, played_at: new Date().toISOString(), repeat: session.mode !== "fresh" });
        setDone({ ...session, status: "completed", ...summarise(cards, results.current), reward: null, kept: true });
      } else setError(e.message + " Your answers are kept — tap Retry.");
    }
  }, [session, uid, cards]);

  const advance = useCallback(() => {
    if (i + 1 >= cards.length) finish();
    else setI(i + 1);
  }, [i, cards.length, finish]);
  function fly(dir: number) {
    if (reduced) { advance(); return; }
    x.set(withTiming(dir * 500, { duration: 180 }, (f) => { if (f) runOnJS(advance)(); }));
  }

  const record = (r: Res) => { results.current = [...results.current.filter((y) => y.card_id !== r.card_id), r]; };

  // Time is up on the card in view. The ring keeps its own seconds (CardClock), so a tick never redraws the card.
  const expire = () => {
    if (!card) return;
    // Only the current visible card expires; future cards are never consumed in background.
    record({ card_id: card.id, outcome: "timed_out", choice: null, ms: LIMIT });
    setCombo(0);
    setExpired(card.id);
  };

  // Auto-advance shortly after an answer locks (Next / swipe stay available).
  useEffect(() => {
    if (choice === null || timedOut || done) return;
    // Wrong answers stay longer so the explanation can actually be read.
    const t = setTimeout(() => fly(1), card && choice !== card.answer ? 2400 : 1000);
    return () => clearTimeout(t);
  }, [choice, card?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (timedOut) { playSfx("wrong", 0.6); buzz("warning"); }
    if (!timedOut) return;
    // Same reading time as a wrong answer: the right option and the short note stay on screen.
    const t = setTimeout(advance, 2400);
    return () => clearTimeout(t);
  }, [timedOut, advance]);

  // Once a card locks, bring the explanation into view on short screens (it sits under the options).
  useEffect(() => {
    if (!locked) return;
    const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: !reduced }), 60);
    return () => clearTimeout(t);
  }, [locked, reduced]);

  function answer(k: number) {
    if (locked || !card) return;
    setPicked({ id: card.id, k });
    const ok = k === card.answer;
    const streak = ok ? combo + 1 : 0;
    setCombo(streak);
    // Diamonds come from fresh sprints only; the flare plays in the gap before the next card.
    const gem = fresh ? gemAt(streak) : null;
    if (gem) setFlare(gem);
    else { buzz(ok ? "success" : "error"); playSfx(ok ? "correct" : "wrong", 0.8); }
    record({ card_id: card.id, outcome: k === card.answer ? "correct" : "incorrect", choice: k, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
  }
  function skip() {
    if (locked || !card) return;
    tap();
    setCombo(0);
    record({ card_id: card.id, outcome: "skipped", choice: null, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
    fly(-1);
  }
  function next() {
    if (choice === null) return;
    tap();
    fly(1);
  }
  // Gesture callbacks run on interaction, not during render; refs hold the clock.
  const pan = Gesture.Pan().activeOffsetX([-15, 15]).onUpdate((e) => { x.set(e.translationX); }).onEnd((e) => {
    if (e.translationX > 110 && choice !== null) runOnJS(next)();
    else if (e.translationX < -110 && choice === null && !timedOut) runOnJS(skip)();
    else x.set(withSpring(0));
  });
  const cardStyle = useAnimatedStyle(() => ({ transform: [{ translateX: x.value }, { rotate: `${x.value / 25}deg` }] }));

  const tint = subjectColor(card?.subject || p.subject);
  const onAgain = () => router.replace({ pathname: "/rapid/session", params: { exam: done?.exam || session?.exam || p.exam, subject: p.subject || cards[0]?.subject || "Physics", chapter: p.chapter || "", picks: p.picks || "", diagrams: p.diagrams || "", weak: p.weak || "", n: String(size), r: uuid() } });
  const examLabel = isBitsat(card?.subject) ? "BITSAT" : session?.exam || done?.exam || p.exam || "";

  return (
    <ArenaBg dim testID="rf-session-screen" style={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom }}>
      <View style={{ flexDirection: "row", alignItems: "center", paddingHorizontal: space.lg, gap: space.md, minHeight: 56 }}>
        <Press testID="rf-exit-button" onPress={() => (done || empty || error && !session ? back() : setExit(true))} accessibilityLabel="Exit session" style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}>
          <Icon name="close" size={22} color={colors.onSurface} />
        </Press>
        <View style={{ flex: 1 }}>
          <T testID="rf-session-exam" w="heavy" size={12} color={colors.onSurfaceSecondary} numberOfLines={1}>{card ? p.weak === "1" ? `Weak Topic · ${done ? (done.label?.split(" · ")[1] || "your weak subtopics") : card.topic || card.chapter}` : `${examLabel} · ${card.subject} · ${done ? (done.chapter || "Mixed chapters") : card.chapter}` : "Rapid Fire"}</T>
          {card && !done ? (
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
              <T w="heavy" size={16} color={colors.onSurfaceInverse} testID="rf-card-counter" numberOfLines={1}>{narrow ? `${i + 1} / ${cards.length}` : `Card ${i + 1} of ${cards.length}`}</T>
              {fresh ? <StreakGem streak={combo} /> : null}
            </View>
          ) : <T w="heavy" size={16} color={colors.onSurfaceInverse}>{done ? "Session complete" : "Loading cards…"}</T>}
        </View>
        {card && !done ? <CardClock key={card.id} startedAt={startedAt} limit={LIMIT} running={!locked} expired={timedOut} color={tint} onExpire={expire} /> : null}
      </View>
      {card && !done ? (cards.length > 30
        // 50 or 100 cards: one smooth bar (thin segments would blur into each other).
        ? <View testID="rf-progress" style={styles.track}><View style={[styles.fill, { width: `${(100 * i) / cards.length}%`, backgroundColor: tint }]} /></View>
        : <View testID="rf-progress" style={{ flexDirection: "row", gap: 2, paddingHorizontal: space.lg, marginBottom: space.md }}>
          {cards.map((c, k) => <View key={c.id} style={{ flex: 1, height: 4, borderRadius: 1, backgroundColor: k < i ? tint : k === i ? colors.onSurfaceInverse : colors.custom_gameLine }} />)}
        </View>
      ) : null}

      {seat.waiting && !card ? <ArenaWait testID="rf-arena-wait" left={seat.left} onCancel={() => { seat.cancel(); back(); }} /> : null}
      {/* Retry takes the message away first: it comes back only if the new try fails too. */}
      {error ? <View style={{ padding: space.lg }}><ErrorBox error={error} retry={() => { setError(""); if (session) finish(); else setN((v) => v + 1); }} testID="rf-error" /></View> : null}
      {empty ? <View style={{ padding: space.lg }}><Card testID="rf-empty"><Empty icon="cards-outline" title={p.weak ? "No weak subtopics yet" : p.revision ? "No missed cards waiting" : "No reviewed cards here yet"} body={p.weak ? "Play a few sprints or matches first. The subtopics you keep missing will build your Weak Topic Sprint." : p.revision ? "These cards may already be cleared or retired. Return to the arena for your latest revision list." : "Only short formula and concept cards appear in Rapid Fire. Try mixed mode or another chapter."} action={<Button testID="rf-empty-back" kind="secondary" label="Back to arena" onPress={back} />} /></Card></View> : null}
      {!card && !error && !empty && !done && !seat.waiting ? <View style={{ padding: space.lg }}><Skeleton h={380} /></View> : null}

      {done ? <Summary s={done} cards={cards} historical={!!p.review} onExit={back} onAgain={onAgain} onRepeat={(ids) => router.replace({ pathname: "/rapid/session", params: { exam: done.exam || p.exam, subject: cards[0]?.subject, ids: ids.join(",") } })} /> : card ? (
        <View style={{ flex: 1, paddingHorizontal: space.lg }}>
          <ScrollView ref={scrollRef} testID="rf-card-scroll" style={styles.scroll} contentContainerStyle={styles.cardArea} showsVerticalScrollIndicator={false}>
            {cards[i + 1] ? <View pointerEvents="none" style={{ position: "absolute", left: 14, right: 14, top: 30, bottom: 6, borderRadius: radius.lg, backgroundColor: tint + "33", borderWidth: 1, borderColor: tint + "88", transform: [{ scale: 0.95 }] }} /> : null}
            <GestureDetector gesture={pan}>
              <Animated.View entering={reduced ? undefined : FadeIn.duration(180)} testID="rf-card" style={[styles.questionCard, { borderColor: locked ? timedOut ? colors.warning : choice === card.answer ? colors.success : colors.error : tint + "66" }, cardStyle]}>
                <View style={{ height: 4, width: 48, borderRadius: 2, backgroundColor: tint }} />
                <RapidText text={card.prompt} size={20} testID="rf-card-prompt" />
                <BiologyDiagram diagram={card.diagram} testID="rf-card-diagram" />
                {locked && card.formula ? <View style={styles.formula}><RapidText text={card.formula} size={21} testID="rf-card-formula" /></View> : null}
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
                        <View style={styles.optionText}><RapidText text={o} size={16} testID={`rf-option-text-${k}`} /></View>
                        {show && isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : show && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
                      </Press>
                    );
                  })}
                </View>
                {locked ? (
                  <View testID="rf-feedback" accessibilityLiveRegion="polite" style={{ gap: 2 }}>
                    <T w="heavy" size={15} color={timedOut ? colors.warning : choice === card.answer ? colors.success : colors.error}>{timedOut ? "⏱ Timed out" : choice === card.answer ? "✓ Correct" : "✗ Incorrect"}</T>
                    {card.explain ? <RapidText text={card.explain} size={14} testID="rf-feedback-explanation" /> : null}
                  </View>
                ) : null}
              </Animated.View>
            </GestureDetector>
          </ScrollView>
          <View style={{ flexDirection: "row", gap: space.sm, paddingVertical: space.md }}>
            <Button testID="rf-skip-button" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={skip} style={{ flex: 1 }} />
            <Button testID="rf-next-button" icon="arrow-right" label={i + 1 >= cards.length ? "Finish" : "Next"} disabled={choice === null} onPress={next} color={colors.custom_amber} style={{ flex: 1.4 }} />
          </View>
          <T size={11} color={colors.muted} style={{ textAlign: "center", paddingBottom: space.sm }}>Tap an option to lock it · swipe right for next · swipe left to skip</T>
        </View>
      ) : null}

      <Sheet visible={exit} onClose={() => setExit(false)} testID="rf-exit-sheet">
        <T w="heavy" size={19}>Leave this session?</T>
        <T testID="rf-exit-explanation" size={13} color={colors.muted}>Finish now to save your answers. Unanswered cards are recorded as skipped, not incorrect.</T>
        <Button testID="rf-exit-finish" label="Finish & see summary" onPress={() => { setExit(false); finish(); }} color={colors.custom_amber} />
        <Button testID="rf-exit-discard" kind="secondary" label="Leave without saving" onPress={back} />
        <Button testID="rf-exit-stay" kind="ghost" label="Keep going" onPress={() => setExit(false)} />
      </Sheet>
      {flare ? <GemFlare key={`${i}-${flare}`} color={flare} onDone={() => setFlare(null)} /> : null}
    </ArenaBg>
  );
}

const styles = StyleSheet.create({
  questionCard: { backgroundColor: colors.custom_reading, borderRadius: 26, padding: 20, gap: 18, borderWidth: 1, shadowColor: colors.custom_gameBg, shadowOpacity: 0.3, shadowRadius: 16, elevation: 4 },
  formula: { padding: 14, backgroundColor: colors.surface, borderRadius: 14 }, optionText: { flex: 1, paddingVertical: 12 },
  scroll: { flex: 1 },
  track: { height: 6, borderRadius: 3, marginHorizontal: space.lg, marginBottom: space.md, backgroundColor: colors.custom_gameLine, overflow: "hidden" },
  fill: { height: 6, borderRadius: 3 },
  cardArea: { flexGrow: 1, justifyContent: "center", paddingVertical: space.sm },
});

export default withRapid(RapidSession, { banner: false });

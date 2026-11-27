// A Solo Sprint played from the phone's own cards: the same rules as the arena's sprint (20 seconds a card, tap to lock,
// skip, the right answer and the short note after every card), and nothing that moves: no card flight, no flares.
// The finished round is kept on the phone and goes up by itself when the server can be reached (./rounds.ts).
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { uuid } from "@/src/api/client";
import { CardClock } from "@/src/rapid/CardClock";
import { RapidDiagram } from "@/src/rapid/Diagram";
import { RapidText } from "@/src/rapid/RapidText";
import { Button, Card, Icon, Press, Sheet, Stat, T, buzz, tap } from "@/src/rapid/ui";
import { CARD_SECONDS, Pick, isBitsat } from "@/src/rapid/scope";
import { playSfx } from "@/src/sfx";
import { rapidColors as colors, radius, space, rapidSubjectColor as subjectColor } from "@/src/theme";
import type { BankCard } from "./bank";
import { Res, keepRound, sendRounds, summarise } from "./rounds";

const LIMIT = CARD_SECONDS * 1000;
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());

export function PlainRound({ uid, cards, picks, repeat, signedIn, onExit, onAgain, onRepeat }: {
  uid: string; cards: BankCard[]; picks: Pick[] | null; repeat?: boolean;
  /** A confirmed session is open: the round is sent at once when the line allows. */
  signedIn: boolean; onExit: () => void; onAgain?: () => void; onRepeat: (cards: BankCard[]) => void;
}) {
  const narrow = useWindowDimensions().width < 360;
  const [i, setI] = useState(0);
  const [picked, setPicked] = useState<{ id: string; k: number } | null>(null);
  const [expired, setExpired] = useState("");
  const [done, setDone] = useState<ReturnType<typeof summarise> | null>(null);
  const [where, setWhere] = useState<"" | "kept" | "sent">("");
  const [reward, setReward] = useState<any>(null);
  const [exit, setExit] = useState(false), [review, setReview] = useState(false);
  const results = useRef<Res[]>([]), startedAt = useRef(0), requestId = useRef(uuid()), finished = useRef(false);
  const scrollRef = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const card = cards[i];
  const choice = picked && picked.id === card?.id ? picked.k : null;
  const timedOut = !!card && expired === card.id;
  const locked = choice !== null || timedOut;
  const tint = subjectColor(card?.subject);

  useEffect(() => {
    if (!card || done) return;
    startedAt.current = mono();
    scrollRef.current?.scrollTo({ y: 0, animated: false });
  }, [card?.id, done]); // eslint-disable-line react-hooks/exhaustive-deps

  const finish = useCallback(async () => {
    if (finished.current) return;
    finished.current = true;
    setDone(summarise(cards, results.current));
    await keepRound(uid, { request_id: requestId.current, picks, card_ids: cards.map((c) => c.id), results: results.current, played_at: new Date().toISOString(), repeat: !!repeat });
    setWhere("kept");
    if (!signedIn) return;
    const out = await sendRounds(uid).catch(() => null);
    if (out && requestId.current in out.rewards) { setReward(out.rewards[requestId.current]); setWhere("sent"); }
  }, [cards, picks, repeat, signedIn, uid]);

  const advance = useRef(() => {});
  advance.current = () => { if (i + 1 >= cards.length) void finish(); else setI(i + 1); };
  const record = (r: Res) => { results.current = [...results.current.filter((y) => y.card_id !== r.card_id), r]; };

  // After an answer the next card comes by itself; a wrong answer stays longer so the note can be read.
  useEffect(() => {
    if (!locked || done || !card) return;
    const timer = setTimeout(() => advance.current(), choice !== null && choice === card.answer ? 1000 : 2400);
    return () => clearTimeout(timer);
  }, [locked, card?.id, done]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!locked) return;
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: false }), 60);
    return () => clearTimeout(timer);
  }, [locked]);

  const expire = () => {
    if (!card || locked) return;
    record({ card_id: card.id, outcome: "timed_out", choice: null, ms: LIMIT });
    playSfx("wrong", 0.6); buzz("warning");
    setExpired(card.id);
  };
  function answer(k: number) {
    if (locked || !card) return;
    const ok = k === card.answer;
    setPicked({ id: card.id, k });
    buzz(ok ? "success" : "error"); playSfx(ok ? "correct" : "wrong", 0.8);
    record({ card_id: card.id, outcome: ok ? "correct" : "incorrect", choice: k, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
  }
  function skip() {
    if (locked || !card) return;
    tap();
    record({ card_id: card.id, outcome: "skipped", choice: null, ms: Math.min(LIMIT, Math.round(mono() - startedAt.current)) });
    advance.current();
  }

  if (done) {
    const sum = done.summary, by = new Map(cards.map((c) => [c.id, c]));
    const missed = done.results.filter((r) => r.outcome !== "correct");
    return <ScrollView testID="rf-plain-summary" contentContainerStyle={styles.summary}>
      <T testID="rf-plain-title" w="heavy" size={22}>{!sum.answered ? "No cards answered" : "Sprint complete"}</T>
      <T testID="rf-plain-where" w="bold" size={13} color={where === "sent" ? colors.success : colors.custom_neonCyan}>
        {where === "sent" ? (reward && Number.isFinite(reward.xp) && Number.isFinite(reward.coins) ? `Round server par pahunch gaya: +${reward.xp} XP · +${reward.coins} coins.` : "Round server par pahunch gaya. Coins aur XP jud gaye.")
          : where === "kept" ? "Yeh round phone par rakha hai. Internet aate hi apne aap bhej diya jayega; coins aur XP tab judenge." : "Round save ho raha hai…"}
      </T>
      <Card style={styles.score}>
        <T w="bold" size={11} color={colors.custom_whiteA70} style={styles.spaced}>SESSION SCORE</T>
        <T w="heavy" size={44} color={colors.onSurfaceInverse} testID="rf-summary-score">{sum.score}<T w="semibold" size={22} color={colors.custom_whiteA70}> / {sum.total}</T></T>
        <T size={13} color={colors.custom_whiteA70}>Answered accuracy {sum.accuracy != null ? sum.accuracy + "%" : "—"} ({sum.correct}/{sum.answered} answered)</T>
      </Card>
      <View style={styles.row}>
        <Stat testID="rf-sum-correct" label="Correct" value={sum.correct} color={colors.success} />
        <Stat testID="rf-sum-incorrect" label="Incorrect" value={sum.incorrect} color={colors.error} />
      </View>
      <View style={styles.row}>
        <Stat testID="rf-sum-skipped" label="Skipped" value={sum.skipped} />
        <Stat testID="rf-sum-timeout" label="Timed out" value={sum.timed_out} color={colors.warning} />
      </View>
      {sum.revise_topics.length ? <Card style={styles.tight} testID="rf-revise-topics">
        <T w="heavy" size={15}>Worth revising (from this session)</T>
        {sum.revise_topics.map((t) => <T key={t} size={13}>• {t}</T>)}
      </Card> : null}
      {missed.length ? <Button testID="rf-review-missed" kind="secondary" icon="eye-outline" label={review ? "Hide review" : `Review ${missed.length} missed card${missed.length > 1 ? "s" : ""}`} onPress={() => setReview(!review)} /> : null}
      {review ? missed.map((m) => {
        const c = by.get(m.card_id);
        return c ? <Card key={c.id} testID={"rf-review-" + c.id} style={styles.reviewed}>
          <T w="bold" size={11} color={colors.muted}>{c.chapter}</T>
          <RapidText testID={`rf-review-prompt-${c.id}`} text={c.prompt} size={16} />
          <RapidDiagram diagram={c.diagram} testID={`rf-review-diagram-${c.id}`} />
          {c.formula ? <RapidText testID={`rf-review-formula-${c.id}`} text={c.formula} size={18} /> : null}
          <RapidText testID={`rf-review-chosen-${c.id}`} size={13} w="regular" color={colors.error} text={m.outcome === "timed_out" ? "⏱ Timed out" : m.outcome === "skipped" ? "↷ Skipped" : `✗ You chose: ${c.options[m.choice as number]}`} />
          <RapidText testID={`rf-review-correct-${c.id}`} size={13} w="bold" color={colors.success} text={`✓ Correct: ${c.options[c.answer]}`} />
          {c.explain ? <RapidText testID={`rf-review-explain-${c.id}`} size={12} w="regular" color={colors.muted} text={c.explain} /> : null}
        </Card> : null;
      }) : null}
      {missed.length ? <Button testID="rf-repeat-missed" icon="repeat" label="Repeat missed cards" color={colors.custom_amber} onPress={() => onRepeat(missed.map((m) => by.get(m.card_id)).filter((c): c is BankCard => !!c))} /> : null}
      {onAgain ? <Button testID="rf-start-another" kind="secondary" icon="lightning-bolt" label="Start another session" onPress={onAgain} /> : null}
      <Button testID="rf-done" kind="ghost" label="Done" onPress={onExit} />
    </ScrollView>;
  }
  if (!card) return null;

  return <View style={styles.flex}>
    <View style={styles.top}>
      <Press testID="rf-exit-button" onPress={() => setExit(true)} accessibilityLabel="Exit session" style={styles.close}><Icon name="close" size={22} color={colors.onSurface} /></Press>
      <View style={styles.flex}>
        <T testID="rf-session-exam" w="heavy" size={12} color={colors.onSurfaceSecondary} numberOfLines={1}>{`${isBitsat(card.subject) ? "BITSAT" : "JEE"} · ${card.subject} · ${card.chapter}`}</T>
        <T w="heavy" size={16} color={colors.onSurfaceInverse} testID="rf-card-counter" numberOfLines={1}>{narrow ? `${i + 1} / ${cards.length}` : `Card ${i + 1} of ${cards.length}`}</T>
      </View>
      <CardClock key={card.id} startedAt={startedAt} limit={LIMIT} running={!locked} expired={timedOut} color={tint} onExpire={expire} />
    </View>
    <View testID="rf-progress" style={styles.track}><View style={[styles.fill, { width: `${(100 * i) / cards.length}%`, backgroundColor: tint }]} /></View>
    <ScrollView ref={scrollRef} testID="rf-card-scroll" style={styles.flex} contentContainerStyle={styles.cardArea} showsVerticalScrollIndicator={false}>
      <View testID="rf-card" style={[styles.card, { borderColor: locked ? (timedOut ? colors.warning : choice === card.answer ? colors.success : colors.error) : tint + "66" }]}>
        <View style={[styles.mark, { backgroundColor: tint }]} />
        <RapidText text={card.prompt} size={20} testID="rf-card-prompt" />
        <RapidDiagram diagram={card.diagram} testID="rf-card-diagram" />
        {locked && card.formula ? <View style={styles.formula}><RapidText text={card.formula} size={21} testID="rf-card-formula" /></View> : null}
        <View style={styles.options}>
          {card.options.map((o, k) => {
            const right = locked && k === card.answer, wrong = locked && k === choice && !right;
            return <Press key={k} testID={"rf-option-" + k} disabled={locked} onPress={() => answer(k)} haptic={false} scaleTo={1} accessibilityLabel={`${o}${right ? ", correct answer" : wrong ? ", your choice, incorrect" : ""}`}
              style={[styles.option, { borderColor: right ? colors.success : wrong ? colors.error : colors.border, backgroundColor: right ? colors.custom_successSoft : wrong ? colors.custom_errorSoft : colors.surfaceSecondary }]}>
              <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
              <View style={styles.optionText}><RapidText text={o} size={16} testID={`rf-option-text-${k}`} /></View>
              {right ? <Icon name="check-circle" size={20} color={colors.success} /> : wrong ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
            </Press>;
          })}
        </View>
        {locked ? <View testID="rf-feedback" accessibilityLiveRegion="polite" style={styles.feedback}>
          <T w="heavy" size={15} color={timedOut ? colors.warning : choice === card.answer ? colors.success : colors.error}>{timedOut ? "⏱ Timed out" : choice === card.answer ? "✓ Correct" : "✗ Incorrect"}</T>
          {card.explain ? <RapidText text={card.explain} size={14} testID="rf-feedback-explanation" /> : null}
        </View> : null}
      </View>
    </ScrollView>
    <View style={styles.keys}>
      <Button testID="rf-skip-button" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={skip} style={styles.flex} />
      <Button testID="rf-next-button" icon="arrow-right" label={i + 1 >= cards.length ? "Finish" : "Next"} disabled={!locked} onPress={() => { tap(); advance.current(); }} color={colors.custom_amber} style={styles.next} />
    </View>
    <Sheet visible={exit} onClose={() => setExit(false)} testID="rf-exit-sheet">
      <T w="heavy" size={19}>Leave this session?</T>
      <T testID="rf-exit-explanation" size={13} color={colors.muted}>Finish now to save your answers. Unanswered cards are recorded as skipped, not incorrect.</T>
      <Button testID="rf-exit-finish" label="Finish & see summary" onPress={() => { setExit(false); void finish(); }} color={colors.custom_amber} />
      <Button testID="rf-exit-discard" kind="secondary" label="Leave without saving" onPress={onExit} />
      <Button testID="rf-exit-stay" kind="ghost" label="Keep going" onPress={() => setExit(false)} />
    </Sheet>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 }, row: { flexDirection: "row", gap: space.sm }, tight: { gap: 4 }, reviewed: { gap: 6 }, spaced: { letterSpacing: 1 },
  summary: { padding: space.lg, gap: space.md },
  score: { alignItems: "center", gap: 4, backgroundColor: colors.surfaceInverse, borderColor: colors.surfaceInverse },
  top: { flexDirection: "row", alignItems: "center", paddingHorizontal: space.lg, gap: space.md, minHeight: 56 },
  close: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border },
  track: { height: 6, borderRadius: 3, marginHorizontal: space.lg, marginBottom: space.md, backgroundColor: colors.custom_gameLine, overflow: "hidden" },
  fill: { height: 6, borderRadius: 3 },
  cardArea: { flexGrow: 1, justifyContent: "center", paddingVertical: space.sm, paddingHorizontal: space.lg },
  card: { backgroundColor: colors.custom_reading, borderRadius: 26, padding: 20, gap: 18, borderWidth: 1 },
  mark: { height: 4, width: 48, borderRadius: 2 },
  formula: { padding: 14, backgroundColor: colors.surface, borderRadius: 14 },
  options: { gap: space.sm },
  option: { minHeight: 52, borderRadius: radius.md, borderWidth: 2, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm },
  optionText: { flex: 1, paddingVertical: 12 }, feedback: { gap: 2 },
  keys: { flexDirection: "row", gap: space.sm, paddingVertical: space.md, paddingHorizontal: space.lg }, next: { flex: 1.4 },
});

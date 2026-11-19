import React, { useCallback, useEffect, useRef, useState } from "react";
import { BackHandler, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeIn, ZoomIn, useReducedMotion } from "react-native-reanimated";
import { Ring } from "@/src/components/Ring";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { Button, ErrorBox, Icon, Press, Sheet, Skeleton, T, buzz, tap, withRapid } from "@/src/rapid/ui";
import { RapidText } from "@/src/rapid/RapidText";
import { playSfx } from "@/src/sfx";
import { ArenaBg, GoldTitle } from "@/src/rapid/arena";
import { DailyResultView } from "@/src/rapid/DailyParts";
import { DailyResult } from "@/src/rapid/daily";
import { rapidColors as colors, radius, space, rapidSubjectColor as subjectColor } from "@/src/theme";

// All India Rapid: the server deals one card at a time and keeps the clock (the phone never holds the answer key).
type PCard = { i: number; subject: string; chapter: string; prompt: string; options: string[] };
type Live = { status: "playing"; i: number; total: number; seconds: number; card: PCard; show_in_ms: number; left_ms: number; correct: number };
type Reveal = { outcome: "correct" | "incorrect" | "timed_out" | "skipped"; answer: number; explain: string; formula: string };
type Reply = (Live & Partial<Reveal>) | ({ status: "done"; result: DailyResult } & Partial<Reveal>);
const mono = () => (globalThis.performance?.now ? globalThis.performance.now() : Date.now());

function DailyRound() {
  const uid = useAuth().user?.id || "";
  const router = useRouter(), insets = useSafeAreaInsets(), reduced = useReducedMotion();
  const [card, setCard] = useState<PCard | null>(null);
  const [total, setTotal] = useState(30), [correct, setCorrect] = useState(0);
  const [limit, setLimit] = useState(20000), [left, setLeft] = useState(20000);
  const [choice, setChoice] = useState<number | null>(null); // -1: timed out or skipped
  const [reveal, setReveal] = useState<Reveal | null>(null);
  const [count, setCount] = useState(0); // 3-2-1 before the first card
  const [result, setResult] = useState<DailyResult | null>(null);
  const [error, setError] = useState(""), [exit, setExit] = useState(false), [n, setN] = useState(0);
  const shownAt = useRef(0), lastTick = useRef(0), timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const retry = useRef<{ i: number; choice: number | null; skip: boolean } | null>(null);
  const scrollRef = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const later = (fn: () => void, ms: number) => { timers.current.push(setTimeout(fn, ms)); };
  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const show = useCallback((s: Live, intro: boolean) => {
    setTotal(s.total); setLimit(s.seconds * 1000);
    const wait = Math.max(0, s.show_in_ms);
    if (intro && wait >= 700) {
      const k = Math.ceil(wait / 1000);
      setCount(k);
      for (let j = 1; j < k; j++) later(() => setCount(k - j), wait - (k - j) * 1000);
    }
    later(() => {
      setCount(0); setCard(s.card); setChoice(null); setReveal(null);
      setLeft(s.left_ms); shownAt.current = mono() - (s.seconds * 1000 - s.left_ms); lastTick.current = 0;
      scrollRef.current?.scrollTo({ y: 0, animated: false });
    }, wait);
  }, []);

  const handle = useCallback((r: Reply, intro: boolean) => {
    if (r.answer !== undefined) {
      setReveal({ outcome: r.outcome!, answer: r.answer, explain: r.explain || "", formula: r.formula || "" });
      const ok = r.outcome === "correct";
      buzz(ok ? "success" : "error"); playSfx(ok ? "correct" : "wrong", ok ? 0.8 : 0.6);
      later(() => scrollRef.current?.scrollToEnd({ animated: !reduced }), 80);
    }
    if (r.status === "done") { later(() => setResult(r.result), r.answer !== undefined ? 1800 : 0); return; }
    setCorrect(r.correct);
    show(r, intro);
  }, [show, reduced]);

  useEffect(() => {
    if (!uid) return;
    let alive = true;
    setError("");
    rf<Reply>("/daily/start", uid, { method: "POST", body: { exam: "JEE" } }).then((r) => { if (alive) handle(r, true); }).catch((e) => { if (alive) setError(e.message); });
    return () => { alive = false; };
  }, [uid, n, handle]);

  const send = useCallback(async (body: { i: number; choice: number | null; skip: boolean }) => {
    retry.current = body;
    try {
      const r = await rf<Reply>("/daily/answer", uid, { method: "POST", body: { exam: "JEE", ...body } });
      retry.current = null; setError("");
      handle(r, r.answer === undefined);
    } catch (e: any) { setError(e.message + " Your answer is safe — tap Retry."); }
  }, [uid, handle]);

  const submit = (k: number | null, skip = false) => {
    if (!card || choice !== null) return;
    setChoice(k ?? -1);
    send({ i: card.i, choice: k, skip });
  };

  // The clock: the server's time left on this card, shown second by second. At zero the card goes to the server as timed out.
  useEffect(() => {
    if (!card || choice !== null || result) return;
    const iv = setInterval(() => {
      const l = limit - (mono() - shownAt.current);
      setLeft((prev) => (Math.ceil(prev / 1000) === Math.ceil(Math.max(0, l) / 1000) ? prev : Math.max(0, l)));
      const sec = Math.ceil(l / 1000);
      if (l > 0 && sec <= 5 && sec !== lastTick.current) { lastTick.current = sec; playSfx("tick", 0.6); }
      if (l <= 0) { clearInterval(iv); submit(null); }
    }, 100);
    return () => clearInterval(iv);
  }, [card?.i, choice, result, limit]); // eslint-disable-line react-hooks/exhaustive-deps

  useFocusEffect(useCallback(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => { if (result) return false; setExit(true); return true; });
    return () => sub.remove();
  }, [result]));

  const finish = async () => {
    setExit(false);
    try { const r = await rf<Reply>("/daily/finish", uid, { method: "POST", body: { exam: "JEE" } }); if (r.status === "done") setResult(r.result); }
    catch (e: any) { setError(e.message); }
  };
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)/rapid"));
  const tint = subjectColor(card?.subject);
  const locked = choice !== null;

  return <ArenaBg dim testID="rf-daily-screen" style={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom }}>
    <View style={styles.top}>
      <Press testID="rf-daily-exit" onPress={() => (result || (!card && error) ? back() : setExit(true))} accessibilityLabel="Leave All India Rapid" style={styles.close}>
        <Icon name="close" size={22} color={colors.onSurface} />
      </Press>
      <View style={styles.flex}>
        <T w="heavy" size={12} color={colors.custom_neonAmber} numberOfLines={1}>ALL INDIA RAPID{card && !result ? ` · ${card.subject} · ${card.chapter}` : ""}</T>
        <T w="heavy" size={16} color={colors.onSurfaceInverse} testID="rf-daily-counter" numberOfLines={1}>{result ? "Round complete" : card ? `Card ${card.i + 1} of ${total} · ${correct} right` : "Getting today’s cards…"}</T>
      </View>
      {card && !result ? <Ring light left={locked ? (reveal?.outcome === "timed_out" ? 0 : left) : left} color={tint} limit={limit} /> : null}
    </View>
    {card && !result ? <View testID="rf-daily-progress" style={styles.bars}>
      {Array.from({ length: total }, (_, k) => <View key={k} style={[styles.seg, { backgroundColor: k < card.i ? tint : k === card.i ? colors.onSurfaceInverse : colors.custom_gameLine }]} />)}
    </View> : null}

    {error ? <View style={styles.pad}><ErrorBox testID="rf-daily-error" error={error} retry={() => { setError(""); if (retry.current) send(retry.current); else setN((v) => v + 1); }} /></View> : null}
    {result ? <DailyResultView result={result} uid={uid} onBack={back} /> : null}
    {!result && !card && !error && !count ? <View style={styles.pad}><Skeleton h={380} /></View> : null}
    {!result && count ? <Animated.View key={count} entering={reduced ? undefined : ZoomIn.duration(260)} style={styles.count} testID="rf-daily-countdown">
      <T w="heavy" size={14} color={colors.custom_neonCyan} style={styles.spaced}>SAME 30 CARDS · ALL OF INDIA</T>
      <GoldTitle size={110} center>{count}</GoldTitle>
      <T w="bold" size={13} color={colors.onSurfaceInverse}>20 seconds a card. Pen down. Go!</T>
    </Animated.View> : null}

    {!result && card && !count ? <View style={styles.body}>
      <ScrollView ref={scrollRef} style={styles.flex} contentContainerStyle={styles.cardArea} showsVerticalScrollIndicator={false}>
        <Animated.View key={card.i} entering={reduced ? undefined : FadeIn.duration(180)} testID="rf-daily-card"
          style={[styles.question, { borderColor: reveal ? (reveal.outcome === "correct" ? colors.success : reveal.outcome === "timed_out" ? colors.warning : colors.error) : tint + "66" }]}>
          <View style={[styles.lip, { backgroundColor: tint }]} />
          <RapidText text={card.prompt} size={20} testID="rf-daily-prompt" />
          {reveal?.formula ? <View style={styles.formula}><RapidText text={reveal.formula} size={20} testID="rf-daily-formula" /></View> : null}
          <View style={styles.options}>
            {card.options.map((o, k) => {
              const isAns = !!reveal && k === reveal.answer, picked = k === choice;
              const bg = isAns ? colors.custom_successSoft : reveal && picked ? colors.custom_errorSoft : picked ? colors.surface : colors.surfaceSecondary;
              const bd = isAns ? colors.success : reveal && picked ? colors.error : picked ? colors.custom_neonCyan : colors.border;
              return <Press key={k} testID={`rf-daily-option-${k}`} disabled={locked} haptic={false} onPress={() => { tap(); submit(k); }}
                accessibilityLabel={`${o}${isAns ? ", correct answer" : reveal && picked ? ", your choice, incorrect" : ""}`} style={[styles.option, { borderColor: bd, backgroundColor: bg }]}>
                <T w="heavy" size={13} color={colors.muted}>{"ABCD"[k]}</T>
                <View style={styles.optionText}><RapidText text={o} size={16} testID={`rf-daily-option-text-${k}`} /></View>
                {isAns ? <Icon name="check-circle" size={20} color={colors.success} /> : reveal && picked ? <Icon name="close-circle" size={20} color={colors.error} /> : null}
              </Press>;
            })}
          </View>
          {reveal ? <View testID="rf-daily-feedback" accessibilityLiveRegion="polite" style={styles.feedback}>
            <T w="heavy" size={15} color={reveal.outcome === "correct" ? colors.success : reveal.outcome === "timed_out" ? colors.warning : colors.error}>
              {reveal.outcome === "correct" ? "✓ Correct" : reveal.outcome === "timed_out" ? "⏱ Timed out" : reveal.outcome === "skipped" ? "↷ Skipped" : "✗ Incorrect"}</T>
            {reveal.explain ? <RapidText text={reveal.explain} size={14} testID="rf-daily-explain" /> : null}
          </View> : locked && !error ? <T size={12} color={colors.muted}>Checking…</T> : null}
        </Animated.View>
      </ScrollView>
      <View style={styles.actions}>
        <Button testID="rf-daily-skip" kind="secondary" icon="skip-next-outline" label="Skip" disabled={locked} onPress={() => submit(null, true)} style={styles.flex} />
      </View>
      <T size={11} color={colors.muted} style={styles.hint}>One try a day · the clock is the server’s · next card comes by itself</T>
    </View> : null}

    <Sheet visible={exit} onClose={() => setExit(false)} testID="rf-daily-exit-sheet">
      <T w="heavy" size={19}>Leave the All India round?</T>
      <T size={13} color={colors.muted}>The clock keeps running on this card. Finish now to put your score on the board — the cards left count as skipped.</T>
      <Button testID="rf-daily-finish" label="Finish & see my rank" onPress={finish} color={colors.custom_amber} />
      <Button testID="rf-daily-leave" kind="secondary" label="Leave for now" onPress={() => { setExit(false); back(); }} />
      <Button testID="rf-daily-stay" kind="ghost" label="Keep playing" onPress={() => setExit(false)} />
    </Sheet>
  </ArenaBg>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, pad: { padding: space.lg }, spaced: { letterSpacing: 1.5 },
  top: { flexDirection: "row", alignItems: "center", paddingHorizontal: space.lg, gap: space.md, minHeight: 56 },
  close: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border },
  bars: { flexDirection: "row", gap: 2, paddingHorizontal: space.lg, marginBottom: space.md }, seg: { flex: 1, height: 4, borderRadius: 1 },
  count: { flex: 1, alignItems: "center", justifyContent: "center", gap: 6, paddingHorizontal: space.lg },
  body: { flex: 1, paddingHorizontal: space.lg },
  cardArea: { flexGrow: 1, justifyContent: "center", paddingVertical: space.sm },
  question: { backgroundColor: colors.custom_reading, borderRadius: 26, padding: 20, gap: 18, borderWidth: 1.5 },
  lip: { height: 4, width: 48, borderRadius: 2 },
  formula: { padding: 14, backgroundColor: colors.surface, borderRadius: 14 },
  options: { gap: space.sm },
  option: { minHeight: 52, borderRadius: radius.md, borderWidth: 2, flexDirection: "row", alignItems: "center", paddingHorizontal: space.md, gap: space.sm },
  optionText: { flex: 1, paddingVertical: 12 },
  feedback: { gap: 2 },
  actions: { flexDirection: "row", gap: space.sm, paddingVertical: space.md },
  hint: { textAlign: "center", paddingBottom: space.sm },
});

export default withRapid(DailyRound, { banner: false });

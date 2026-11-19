import React, { useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { Icon, IconName, T } from "@/src/components/ui";
import { Pill, RoundButton } from "@/src/components/design";
import { colors, radius, space } from "@/src/theme";

const R = 54, C = 2 * Math.PI * R;
const signed = (n: number) => (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n);

/** The minute before the paper (website get-ready): rules, the whole paper loading, Begin now. */
function rules(a: any): [IconName, string][] {
  const { correct = 4, wrong = -1, minutes } = a.rules || {};
  const result = a.mode === "series_live" ? "Submit and your score and solutions open right away. Your All India rank for today joins at 11:59 PM."
    : a.competition_end ? "Submit and your score shows right away. Solutions open when the exam closes for everyone." : "Submit and your score and solutions open right away.";
  return [
    ["plus-minus-variant", `${signed(correct)} for a right answer, ${signed(wrong)} for a wrong one, 0 for a skip. Not sure? A smart skip beats a wild guess.`],
    ["clock-outline", minutes ? `${minutes} minutes on your clock. It starts only when you press Begin now or this countdown reaches zero.` : "No clock today. Take your time and think it through."],
    ["content-save-check-outline", "Every answer saves by itself. Watch for “Saved” at the top."],
    ["flag-outline", "Stuck? Mark it for review, move on, come back later. You can jump to any question anytime."],
    ["wifi-off", "Net dropped? Keep solving. Your answers wait safely on this phone and send when you are back."],
    ["trophy-outline", result],
  ];
}

export function GetReady({ attempt, seconds, loaded, onBegin, onLeave }: {
  attempt: any; seconds: number; loaded: { done: number; total: number }; onBegin: () => Promise<void>; onLeave: () => void;
}) {
  const insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const ready = loaded.total === 0 || loaded.done >= loaded.total;
  const percent = loaded.total ? Math.round((100 * loaded.done) / loaded.total) : 100;
  const begin = async () => {
    setBusy(true); setError("");
    try { await onBegin(); } catch (e: any) { setError(e?.message || "Couldn't open the paper. Please retry."); setBusy(false); }
  };
  return (
    <ScrollView testID="get-ready-screen" style={styles.screen} contentContainerStyle={[styles.content, { paddingTop: insets.top + space.sm, paddingBottom: insets.bottom + space.xl }]}>
      <View style={styles.top}>
        <RoundButton testID="get-ready-leave" icon="close" label="Leave attempt" color={colors.onSurface} onPress={onLeave} />
        <T testID="get-ready-kicker" w="heavy" size={11} color={colors.brandText} style={styles.kicker}>GET SET · 60 SECONDS</T>
        <View style={styles.side} />
      </View>
      <View style={styles.hero}>
        <View testID="get-ready-countdown" accessibilityRole="timer" accessibilityLabel={`${seconds} seconds left`} style={styles.ring}>
          <Svg width={132} height={132} viewBox="0 0 120 120" style={styles.svg}>
            <Circle cx={60} cy={60} r={R} stroke={colors.custom_cardLine} strokeWidth={8} fill="none" />
            <Circle cx={60} cy={60} r={R} stroke={colors.brandPrimary} strokeWidth={8} fill="none" strokeLinecap="round"
              strokeDasharray={`${C}`} strokeDashoffset={C * (1 - Math.min(60, seconds) / 60)} />
          </Svg>
          <T testID="get-ready-seconds" w="mono" size={40}>{seconds}</T>
          <T w="bold" size={11} color={colors.muted} style={styles.sec}>SEC</T>
        </View>
        <T testID="get-ready-title" w="heavy" size={24} style={styles.center}>Deep breath. You’ve got this.</T>
        <T testID="get-ready-paper" size={13} color={colors.muted} style={styles.center}>{attempt.title} · {attempt.count ?? attempt.questions?.length} questions{attempt.rules?.minutes ? ` · ${attempt.rules.minutes} minutes` : ""}</T>
      </View>
      <View testID="get-ready-rules" style={styles.card}>
        {rules(attempt).map(([icon, text], i) => (
          <Animated.View key={icon} entering={reduced ? undefined : FadeInDown.delay(90 * i).duration(360)} style={[styles.rule, i > 0 && styles.ruleLine]}>
            <View style={styles.ruleIcon}><Icon name={icon} size={18} color={colors.onSurface} /></View>
            <T size={13} color={colors.custom_softText} style={styles.grow}>{text}</T>
          </Animated.View>
        ))}
      </View>
      <View testID="get-ready-load" style={[styles.load, ready && styles.loadDone]}>
        <View style={styles.loadRow}>
          {ready ? <Icon name="check-circle" size={17} color={colors.success} /> : <ActivityIndicator size="small" color={colors.brandPrimary} />}
          <T testID="get-ready-load-text" w="bold" size={13} color={ready ? colors.success : colors.onSurface} style={styles.grow}>
            {ready ? "Whole paper loaded" : `Loading your paper · ${loaded.done} / ${loaded.total} pictures`}
          </T>
          <T testID="get-ready-load-percent" w="mono" size={13} color={ready ? colors.success : colors.onSurface}>{percent}%</T>
        </View>
        <View style={styles.bar}><View style={[styles.fill, { width: `${percent}%`, backgroundColor: ready ? colors.success : colors.brandPrimary }]} /></View>
      </View>
      {error ? <T testID="get-ready-error" size={13} color={colors.error} accessibilityRole="alert">{error}</T> : null}
      <Pill testID="get-ready-begin" kind="brand" size="lg" label={ready ? "Begin now" : "Loading paper…"} icon="arrow-right" busy={busy} disabled={!ready || busy} onPress={begin} />
      <T testID="get-ready-note" size={12} color={colors.muted} style={styles.center}>
        {ready ? `Or relax. The paper opens by itself in ${seconds} s.` : "The paper opens by itself when the countdown ends. Loading keeps going in the background."}
      </T>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  content: { width: "100%", maxWidth: 560, alignSelf: "center", paddingHorizontal: space.lg, gap: space.lg },
  top: { flexDirection: "row", alignItems: "center", gap: space.sm },
  kicker: { flex: 1, textAlign: "center", letterSpacing: 1.8 }, side: { width: 44 },
  hero: { alignItems: "center", gap: space.sm },
  ring: { width: 132, height: 132, alignItems: "center", justifyContent: "center", marginBottom: space.sm },
  svg: { position: "absolute", transform: [{ rotate: "-90deg" }] },
  sec: { letterSpacing: 1.5, marginTop: -4 },
  center: { textAlign: "center" },
  card: { backgroundColor: colors.custom_card, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLine, paddingHorizontal: space.lg },
  rule: { flexDirection: "row", alignItems: "flex-start", gap: space.md, paddingVertical: space.md },
  ruleLine: { borderTopWidth: 1, borderTopColor: colors.custom_cardLine },
  ruleIcon: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.custom_cardRaised, alignItems: "center", justifyContent: "center" },
  grow: { flex: 1, minWidth: 0 },
  load: { gap: space.sm, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card },
  loadDone: { borderColor: colors.success, backgroundColor: colors.custom_successSoft },
  loadRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  bar: { height: 6, borderRadius: radius.pill, backgroundColor: colors.custom_cardLine, overflow: "hidden" },
  fill: { height: "100%", borderRadius: radius.pill },
});

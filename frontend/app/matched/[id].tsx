// One JEE Main shift on Matched: its top card (how many questions matched, and "Attempt all matched"), then every
// question that matched on its own card: the JEE question, ours under it, and the solution of both.
// Open to everyone, signed in or not. Attempting is for students with an account: the button opens the shift's real
// paper on jeelive.ai (started, solved, marked and analysed like every other paper); without an account it asks to sign up.
import React, { useEffect, useMemo, useState } from "react";
import { FlatList, RefreshControl, View, useWindowDimensions } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { Empty, ErrorBox, Skeleton, T } from "@/src/components/ui";
import { DSheet, Pill, ScreenHeader } from "@/src/components/design";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space } from "@/src/theme";
import { MatchedShift, SHORT, dayLabel, getShift, yearOf } from "@/src/matched/api";
import { AttemptCard } from "@/src/matched/MatchedCard";
import { Pair } from "@/src/matched/Pair";
import { PAD, kept } from "@/src/matched/parts";

export default function MatchedShiftScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const [asking, setAsking] = useState(false);
  // A shift can be long: kept in memory while the app is open, not written to the phone.
  const res = useCached<MatchedShift>(id ? `matched.shift.${id}` : null, getShift(id), false);
  const d = res.data;
  const [subject, setSubject] = useState("");
  useEffect(() => () => kept.clear(), []);
  const subjects = d?.subjects || [];
  const on = subjects.some(s => s.name === subject) ? subject : "";
  const rows = useMemo(() => (d?.items || []).map((it, k) => ({ it, k })), [d]);
  const shown = useMemo(() => rows.filter(r => !on || r.it.subject === on), [rows, on]);
  // What is left of the screen's width inside a card, for the pictures.
  const width = Math.min(useWindowDimensions().width, 720) - 2 * space.lg - 2 * PAD - 2;
  const year = d ? yearOf(d.day) : "", where = d ? `${dayLabel(d.day)} · Shift ${d.shift}` : "";
  const toEntry = (mode: "signup" | "login") => { setAsking(false); router.push({ pathname: "/entry", params: { mode, next: `/matched/${id}` } }); };
  return <ScreenMotion>
    <View testID="matched-shift-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="matched-shift-header" title={d ? `Shift ${d.shift} · ${dayLabel(d.day)}` : "Matched"} eyebrow={d ? `JEE Main ${year}` : "JEE Main"}
        backTestID="matched-shift-back" onBack={() => (router.canGoBack() ? router.back() : router.replace("/matched" as any))} />
      <FlatList testID="matched-shift-list" data={shown} keyExtractor={r => String(r.k)}
        renderItem={({ item }) => <Pair it={item.it} k={item.k} width={width} year={year} where={where} />}
        // A question with maths holds a typesetter: only the few near the screen are kept drawn.
        initialNumToRender={3} maxToRenderPerBatch={3} windowSize={5} showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        refreshControl={<RefreshControl testID="matched-shift-refresh" refreshing={res.refreshing} onRefresh={res.reload} />}
        ListHeaderComponent={<View style={{ gap: space.md }}>
          <ErrorBox testID="matched-shift-error" error={res.error} retry={res.reload} />
          {!d && !res.error ? <View testID="matched-shift-loading" style={{ gap: space.md }}><Skeleton h={96} /><Skeleton h={220} /></View> : null}
          {d ? <AttemptCard matched={d.matched} asked={d.asked} year={year} questions={d.paper_id ? d.paper_questions || 0 : 0}
            note={user ? "Hamare woh sawaal jo JEE Main mein match hue, ek paper mein.\nTimer, result, analysis aur solutions: har paper ki tarah."
              : "Dekhna sabke liye khula hai.\nPaper attempt karne ke liye free account banao."}
            onAttempt={() => (user ? router.push(`/set/${d.paper_id}`) : setAsking(true))} /> : null}
          {d?.items.length ? <T testID="matched-shift-list-title" w="bold" size={12} color={colors.custom_eyebrow} style={{ letterSpacing: 1.6, marginTop: space.xs }}>KAUN SA SAWAAL KISSE MATCH HUA</T> : null}
          {subjects.length > 1 ? <PillRow prefix="matched-subject" value={on} onChange={setSubject}
            items={[{ key: "", label: "All", count: d!.matched }, ...subjects.map(s => ({ key: s.name, label: SHORT[s.name] || s.name, count: s.n }))]} /> : null}
        </View>}
        ListEmptyComponent={d ? <Empty testID="matched-shift-empty" icon="calendar-check-outline" title="Is shift mein koi match nahi mila" body="Doosre shifts dekhne ke liye wapas jao." /> : undefined} />
      <DSheet testID="matched-signup-sheet" visible={asking} onClose={() => setAsking(false)} title="Sign up karke attempt karo" scroll={false}>
        <T testID="matched-signup-text" size={14} color={colors.custom_softText} style={{ lineHeight: 21 }}>
          Matched sawaal dekhna sabke liye khula hai. Inhe paper ki tarah attempt karne ke liye (timer, result, analysis aur solutions ke saath) free account banao: sirf mobile number aur PIN.
        </T>
        <Pill testID="matched-signup-yes" size="lg" label="Free account banao" iconRight="arrow-right" onPress={() => toEntry("signup")} />
        <Pill testID="matched-signup-login" kind="outline" label="Mera account hai · Sign in" onPress={() => toEntry("login")} />
      </DSheet>
    </View>
  </ScreenMotion>;
}

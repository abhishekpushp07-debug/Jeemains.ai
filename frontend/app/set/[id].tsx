import React, { useEffect, useRef, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api, del, post, uuid } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { invalidate } from "@/src/useCached";
import { ErrorBox, Icon, Notice, Skeleton, T } from "@/src/components/ui";
import { DCard, Pill, RoundButton, ScreenHeader, SectionLabel } from "@/src/components/design";
import { colors, radius, space, subjectColor } from "@/src/theme";
import { checkReadiness } from "@/src/api/readiness";
import { warmAttempt } from "@/src/api/paperOpening";
import { track } from "@/src/jlTracker";

export default function SetDetail() {
  const { id, start: auto } = useLocalSearchParams<{ id: string; start?: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [s, setS] = useState<any>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [reload, setReload] = useState(0);
  const key = useRef<string | null>(null);
  const [keyed, setKeyed] = useState(false); // this start's retry key has been read from the phone
  const autoStarted = useRef(false);
  const startKeyName = `start.${user?.id}.${id}`;

  useEffect(() => {
    let alive = true;
    api(`${user ? "/my/sets/" : "/sets/"}${id}`).then((d) => { if (alive) { setError(""); setS(d); setSaved(!!d.saved); track("test_card_viewed", { set_id: String(id) }); } }).catch((e) => alive && setError(e.message));
    storage.getItem<string | null>(startKeyName, null).then(async (k) => {
      key.current = k || uuid();
      if (!k) await storage.setItem(startKeyName, key.current);
      if (alive) setKeyed(true);
    });
    return () => { alive = false; };
  }, [id, user, reload, startKeyName]);

  // Opened with start=1 (the "Shuru karein?" sheet of a missed All India day, already confirmed there): the same checked
  // start below runs once by itself. If it cannot start, this page stays with the reason and its usual Start button.
  useEffect(() => {
    if (auto !== "1" || autoStarted.current || !s || !user || !keyed) return;
    autoStarted.current = true;
    if (s.attempt?.status === "active") { void warmAttempt(s.attempt.id); router.replace(`/attempt/${s.attempt.id}`); }
    else void start();
  }, [auto, s, user, keyed]); // eslint-disable-line react-hooks/exhaustive-deps

  // One tap: the device/connection check the server needs runs silently, then the attempt opens.
  async function start(checkedAt = 0) {
    track("test_start_clicked", { set_id: String(id) }); // the tap only: the website alone says what an attempt did
    setBusy(true);
    setError("");
    try {
      if (!checkedAt || Date.now() - checkedAt > 60000) await checkReadiness(id!);
      key.current ||= uuid();
      if (!await storage.setItem(startKeyName, key.current)) throw new Error("Device storage is unavailable. Please retry before starting.");
      // Same start_key on every retry of this intent → no duplicate attempts.
      const a = await post(`/sets/${id}/start`, { start_key: key.current, device_checked: true, preview: false, get_ready: true });
      if (!a?.id) throw new Error("The start could not be confirmed. Your retry key is preserved.");
      void warmAttempt(a.id, a);
      await storage.removeItem(startKeyName);
      invalidate(`u.${user?.id}.`);
      router.replace((a.status === "completed" ? "/result/" : "/attempt/") + a.id as any);
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  }
  async function toggleSave() {
    try {
      if (saved) await del(`/my/tests/saved/${id}`);
      else await post(`/my/tests/saved/${id}`, {});
      setSaved(!saved);
      invalidate(`u.${user?.id}.tests`);
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (!s) return (
    <View style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader title="Loading paper…" onBack={() => router.back()} />
      <View style={{ padding: space.lg, gap: space.md }}>{error ? <ErrorBox error={error} retry={() => setReload((n) => n + 1)} /> : <><Skeleton h={140} /><Skeleton h={220} /></>}</View>
    </View>
  );
  const count = s.count ?? s.questions?.length;
  const minutes = s.rules?.minutes;
  const subj = s.chapter_subject;
  const facts: [string, string | number, string][] = [["Questions", count, "set-question-count"], [minutes ? "Minutes" : "Untimed", minutes || "—", "set-duration"], ["Max marks", s.maximum ?? count * s.rules.correct, "set-maximum-marks"]];
  return (
    <View testID="set-detail-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader title={s.title} eyebrow={`${s.exam} · ${s.series_id ? "All India series" : s.test_kind === "chapter" ? "Chapter practice" : s.test_kind === "pyq" ? "Previous-year paper" : s.test_kind === "choice" ? "Student Choice" : s.test_kind === "matched" ? "Matched paper" : s.test_kind === "misfire" ? "Misfire Mock" : "Full mock"}`} eyebrowColor={subj ? subjectColor(subj) : undefined} onBack={() => router.back()}
        right={<RoundButton testID="set-save-toggle" icon={saved ? "bookmark" : "bookmark-outline"} color={colors.custom_gold} active={saved} label={saved ? "Unsave paper" : "Save paper"} onPress={toggleSave} />} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingTop: space.xs, paddingBottom: insets.bottom + space.xl, gap: space.lg }}>
        <DCard testID="set-facts" style={{ gap: space.lg }}>
          <View style={styles.facts}>
            {facts.map(([label, value, testID], i) => <View key={testID} testID={testID} style={[styles.fact, i > 0 && styles.factLine]}>
              <T w="heavy" size={24}>{String(value)}</T>
              <T size={11.5} color={colors.custom_eyebrow}>{label}</T>
            </View>)}
          </View>
          <View testID="set-marking-rule" style={{ flexDirection: "row", gap: space.sm, flexWrap: "wrap" }}>
            {[[`+${s.rules.correct} correct`, colors.custom_mint], [`${s.rules.wrong} incorrect`, colors.error], [`${s.rules.skipped ?? 0} unanswered`, colors.muted]].map(([l, c]) => (
              <View key={l} style={[styles.rule, { borderColor: c }]}><T w="bold" size={12} color={c}>{l}</T></View>
            ))}
          </View>
          {s.types ? <T size={12} color={colors.muted}>{s.types.mcq ?? 0} MCQ · {s.types.integer ?? 0} integer</T> : null}
        </DCard>
        <View style={{ gap: space.sm }}>
          <SectionLabel title="Before you start" />
          <DCard testID="set-instructions" style={{ gap: space.md }}>
            {[
              "One correct option per question, or an exact integer where stated. Mark for review and return anytime.",
              s.rules.numeric_rule,
              minutes ? "You get a 60-second get-ready while the whole paper loads. Your clock starts only when you press Begin now or the countdown ends, and keeps running if you disconnect or leave the app. Only answers the server receives before the deadline are scored." : "Untimed practice — come back to your saved attempt whenever you need.",
              s.series_id ? "Live results and solutions are sealed until 11:59 PM IST." : s.solution_kind === "answer_key_only" ? "Submitting is final. Score and supplied answer keys appear after grading. This book has no worked solutions." : "Submitting is final. Your result and supplied solutions appear afterwards.",
              s.test_kind === "chapter" ? "This is chapter practice, not a full exam simulation. Rank estimates are not shown for chapter scores." : null,
            ].filter(Boolean).map((x: any) => (
              <View key={x} style={{ flexDirection: "row", gap: space.sm, alignItems: "flex-start" }}><Icon name="check-circle-outline" size={17} color={colors.custom_softText} style={{ marginTop: 1 }} /><T size={13} color={colors.custom_softText} style={{ flex: 1 }}>{x}</T></View>
            ))}
          </DCard>
        </View>
        <Notice tone="info" icon="content-save-outline" testID="set-offline-notice">Your drafts stay on this phone if the internet drops. They show as Pending until the server confirms them — check the save status before submitting.</Notice>
        <ErrorBox error={error} testID="set-error" />
        {user ? (
          <>
            <Pill testID="set-start-button" size="lg" label={s.attempt?.status === "active" ? "Resume attempt" : "Start attempt"} icon="play" busy={busy} onPress={() => { if (s.attempt?.status === "active") { void warmAttempt(s.attempt.id); router.replace(`/attempt/${s.attempt.id}`); } else void start(); }} />
            <T testID="set-start-note" size={11} color={colors.custom_eyebrow} style={{ textAlign: "center" }}>Starting accepts the rules above. A 60-second get-ready comes first; your official timer starts after it.</T>
          </>
        ) : <Pill testID="set-signin-button" size="lg" label="Sign in to start" onPress={() => router.push("/entry")} />}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  facts: { flexDirection: "row" },
  fact: { flex: 1, gap: 2, paddingHorizontal: space.sm },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_cardLine },
  rule: { paddingHorizontal: 12, height: 30, justifyContent: "center", borderRadius: radius.pill, borderWidth: 1 },
});
